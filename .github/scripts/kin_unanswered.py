# 네이버 지식iN에서 '아직 답변이 안 달린' 관세·통관 질문을 추려 research/에 저장한다.
# 1차: 관세/무역/직구 관련 디렉터리의 '답변 대기' 목록 페이지를 러너에서 긁어 질문 링크 수집.
# 2차: 검색 API(sort=date)로도 최근 질문 보강.
# 각 후보의 실제 답변 수를 질문 페이지에서 확인해 0개만 남긴다.
# 사용: NAVER_CLIENT_ID/SECRET, KEYWORDS(쉼표), WANT(기본 8), MAX_FETCH(기본 120)
import os, re, json, html, datetime, urllib.parse, urllib.request

CID = os.environ.get("NAVER_CLIENT_ID", "").strip()
CSEC = os.environ.get("NAVER_CLIENT_SECRET", "").strip()
KEYWORDS = [k.strip() for k in os.environ.get(
    "KEYWORDS", "해외직구 관세,통관,개인통관고유부호,관부가세,직구 세금,영양제 직구,배대지").split(",") if k.strip()]
WANT = int(os.environ.get("WANT", "8") or 8)
MAX_FETCH = int(os.environ.get("MAX_FETCH", "120") or 120)
KST = datetime.timezone(datetime.timedelta(hours=9))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

# 관세·무역·직구·통관이 몰리는 지식iN 디렉터리(dirId)
# 5040106 = 쇼핑>해외직구 (직구 질문 핵심), 40310/40502 = 경제>무역/관세, 512 = 쇼핑
DIRS = ["5040106", "40310", "40502", "512", "40501"]


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return ""


def open_list_links(dir_id):
    """디렉터리의 '답변 대기(미해결)' 질문 목록에서 질문 링크를 뽑는다."""
    urls = [
        f"https://m.kin.naver.com/mobile/qna/openList.naver?dirId={dir_id}",
        f"https://kin.naver.com/qna/kinupList.naver?dirId={dir_id}",
        f"https://kin.naver.com/qna/list.naver?dirId={dir_id}&sortType=none",
    ]
    found = []
    for u in urls:
        h = get(u)
        if not h:
            continue
        for m in re.finditer(r'/qna/detail\.naver\?[^"\'<> ]*docId=(\d+)[^"\'<> ]*', h):
            frag = m.group(0).replace("&amp;", "&")
            found.append("https://kin.naver.com" + frag)
        if found:
            break
    return found


def search_api_links():
    if not (CID and CSEC):
        return []
    combos = [
        ("https://openapi.naver.com/v1/search/kin.json",
         {"X-Naver-Client-Id": CID, "X-Naver-Client-Secret": CSEC}),
    ]
    out = []
    for kw in KEYWORDS:
        qs = urllib.parse.urlencode({"query": kw, "display": 100, "sort": "date", "format": "json"})
        for url, headers in combos:
            try:
                with urllib.request.urlopen(urllib.request.Request(f"{url}?{qs}", headers=headers), timeout=30) as r:
                    items = json.load(r).get("items", [])
                out += [it.get("link", "") for it in items if "kin.naver.com" in it.get("link", "")]
                break
            except Exception as e:
                print(f"::warning::검색 실패 {kw}: {e}")
    return out


def detail(url):
    """질문 페이지에서 (답변수, 제목). 답변수 미확인이면 (-1, title)."""
    m = re.search(r"docId=(\d+)", url)
    if not m:
        return -1, ""
    d1 = re.search(r"d1id=(\d+)", url)
    dr = re.search(r"dirId=(\d+)", url)
    murl = "https://m.kin.naver.com/mobile/qna/detail.naver?" + urllib.parse.urlencode(
        {k: v for k, v in [("d1id", d1.group(1) if d1 else None),
                            ("dirId", dr.group(1) if dr else None),
                            ("docId", m.group(1))] if v})
    h = get(murl)
    if not h:
        return -1, ""
    title = ""
    mt = re.search(r'<meta property="og:title" content="([^"]*)"', h) or re.search(r"<title>([^<]*)</title>", h)
    if mt:
        title = html.unescape(mt.group(1)).replace(" : 지식iN", "").replace("네이버 지식iN", "").strip()
    if any(s in h for s in ("아직 답변이 없습니다", "첫 번째 답변", "등록된 답변이 없습니다", "답변을 기다리는")):
        return 0, title
    mm = re.search(r'"answerCount"\s*:\s*(\d+)', h) or re.search(r'답변\s*(\d+)\s*개', h)
    if mm:
        return int(mm.group(1)), title
    return -1, title


def main():
    now = datetime.datetime.now(KST)
    candidates = []
    for d in DIRS:
        links = open_list_links(d)
        print(f"[목록] dir {d}: 질문 링크 {len(links)}건")
        candidates += links
    candidates += search_api_links()
    # 중복 제거(docId 기준)
    seen, uniq = set(), []
    for u in candidates:
        did = re.search(r"docId=(\d+)", u)
        if did and did.group(1) not in seen:
            seen.add(did.group(1))
            uniq.append(u)
    print(f"후보 {len(uniq)}건(중복 제외) — 답변수 확인 시작")

    # 관세·직구·통관 관련 제목만 남기기 위한 키워드
    TOPIC = re.compile(r"관세|관부가세|통관|직구|해외구매|면세|배대지|배송대행|개인통관|유니패스|"
                       r"관세청|알리|테무|아마존|아이허브|타오바오|이베이|직배송|구매대행|"
                       r"부가세|HS코드|전파인증|반품.*관세|영양제.*직구|직구.*세금|합산과세")
    unanswered, fetched = [], 0
    for u in uniq:
        if fetched >= MAX_FETCH or len(unanswered) >= WANT:
            break
        fetched += 1
        cnt, title = detail(u)
        if cnt == 0 and title and TOPIC.search(title):
            unanswered.append((title, u))
            print(f"[미답변] {title[:40]}")

    lines = [f"# 지식iN 미답변 질문 — {now:%Y-%m-%d %H:%M} (KST)", "",
             f"후보 {len(uniq)} · 조회 {fetched} · 미답변 {len(unanswered)}건", ""]
    for t, u in unanswered:
        lines.append(f"- {t}\n  {u}")
    os.makedirs("research", exist_ok=True)
    path = f"research/지식인-미답변-{now:%Y%m%d-%H%M}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n저장: {path} — 미답변 {len(unanswered)}건")
    if not unanswered:
        print("::warning::미답변 질문 0건 — 목록 엔드포인트 구조가 바뀌었을 수 있음.")


if __name__ == "__main__":
    main()
