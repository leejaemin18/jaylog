# 네이버 지식iN에서 '아직 답변이 안 달린' 최근 질문을 추려 research/에 저장한다.
# 방법: 검색 API(sort=date)로 최근 질문 URL 수집 → 각 질문 페이지를 러너에서 열어 답변 수 확인 → 0개만 추림.
# 사용: NAVER_CLIENT_ID/SECRET, KEYWORDS(쉼표), WANT(원하는 미답변 개수, 기본 8), MAX_FETCH(최대 조회, 기본 60)
import os, re, json, html, datetime, urllib.parse, urllib.request

CID = os.environ["NAVER_CLIENT_ID"].strip()
CSEC = os.environ["NAVER_CLIENT_SECRET"].strip()
KEYWORDS = [k.strip() for k in os.environ.get(
    "KEYWORDS", "해외직구 관세,통관,개인통관고유부호,관부가세,직구 세금").split(",") if k.strip()]
WANT = int(os.environ.get("WANT", "8") or 8)
MAX_FETCH = int(os.environ.get("MAX_FETCH", "60") or 60)
KST = datetime.timezone(datetime.timedelta(hours=9))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")

COMBOS = [
    ("https://openapi.naver.com/v1/search/kin.json",
     {"X-Naver-Client-Id": CID, "X-Naver-Client-Secret": CSEC}),
    ("https://naverapihub.apigw.ntruss.com/search/v1/kin",
     {"X-NCP-APIGW-API-KEY-ID": CID, "X-NCP-APIGW-API-KEY": CSEC}),
]
working = None


def search(keyword):
    global working
    qs = urllib.parse.urlencode({"query": keyword, "display": 100, "sort": "date", "format": "json"})
    for url, headers in ([working] if working else COMBOS):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"{url}?{qs}", headers=headers), timeout=30) as r:
                data = json.load(r)
            working = (url, headers)
            return data.get("items", [])
        except Exception as e:
            print(f"::warning::검색 실패 {url}: {e}")
    return []


def clean(s):
    return html.unescape(re.sub(r"</?b>", "", s)).strip()


def answer_count(url):
    """질문 페이지를 열어 답변 수를 추정. 미확인이면 -1."""
    # 모바일 페이지가 서버렌더라 파싱이 쉽다.
    m = re.search(r"docId=(\d+)", url)
    d1 = re.search(r"d1id=(\d+)", url)
    dir_ = re.search(r"dirId=(\d+)", url)
    if not m:
        return -1
    murl = "https://m.kin.naver.com/mobile/qna/detail.naver?" + urllib.parse.urlencode(
        {k: v for k, v in [("d1id", d1.group(1) if d1 else None),
                            ("dirId", dir_.group(1) if dir_ else None),
                            ("docId", m.group(1))] if v})
    try:
        req = urllib.request.Request(murl, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko"})
        with urllib.request.urlopen(req, timeout=20) as r:
            h = r.read().decode("utf-8", "replace")
    except Exception:
        return -1
    # 미답변 신호
    if ("아직 답변이 없습니다" in h or "첫 번째 답변" in h or "답변을 기다리는 질문" in h
            or "등록된 답변이 없습니다" in h):
        return 0
    # answerCount JSON 필드
    mm = re.search(r'"answerCount"\s*:\s*(\d+)', h)
    if mm:
        return int(mm.group(1))
    mm = re.search(r'답변\s*(\d+)\s*개', h)
    if mm:
        return int(mm.group(1))
    return -1


def main():
    now = datetime.datetime.now(KST)
    seen, unanswered, fetched = set(), [], 0
    for kw in KEYWORDS:
        for it in search(kw):
            link = it.get("link", "")
            if not link or "kin.naver.com" not in link or link in seen:
                continue
            seen.add(link)
            if fetched >= MAX_FETCH or len(unanswered) >= WANT:
                break
            fetched += 1
            cnt = answer_count(link)
            if cnt == 0:
                unanswered.append((clean(it.get("title", "")), link, kw))
                print(f"[미답변] {clean(it.get('title',''))[:36]}")
        if len(unanswered) >= WANT:
            break
    lines = [f"# 지식iN 미답변 질문 — {now:%Y-%m-%d %H:%M} (KST)", "",
             f"조회 {fetched}건 중 답변 0개 {len(unanswered)}건 (키워드: {', '.join(KEYWORDS)})", ""]
    for t, l, kw in unanswered:
        lines.append(f"- [{kw}] {t}\n  {l}")
    os.makedirs("research", exist_ok=True)
    path = f"research/지식인-미답변-{now:%Y%m%d-%H%M}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n저장: {path} — 미답변 {len(unanswered)}건 / 조회 {fetched}건")
    if not unanswered:
        print("::warning::미답변 질문을 찾지 못함(네이버가 러너 접근을 막았거나 최근 질문이 모두 답변됨).")


if __name__ == "__main__":
    main()
