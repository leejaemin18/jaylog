# 네이버 지식iN 검색 API로 질문 목록을 수집해 research/ 폴더에 저장하는 스크립트.
# 사용: 환경변수 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, KEYWORDS(쉼표 구분), DISPLAY(선택, 기본 50)
# 네이버가 구 개발자센터/신 클라우드 API HUB 두 방식이 있어, 되는 조합을 자동 탐지한다.
import os, re, json, html, datetime, urllib.parse, urllib.request

CID = os.environ["NAVER_CLIENT_ID"].strip()
CSEC = os.environ["NAVER_CLIENT_SECRET"].strip()
KEYWORDS = [k.strip() for k in os.environ.get("KEYWORDS", "해외직구 관세").split(",") if k.strip()]
DISPLAY = min(int(os.environ.get("DISPLAY", "50") or 50), 100)
KST = datetime.timezone(datetime.timedelta(hours=9))

# (엔드포인트, 헤더) 후보 — 위에서부터 시도해 처음 성공하는 조합 사용
COMBOS = [
    ("https://openapi.naver.com/v1/search/kin.json",
     {"X-Naver-Client-Id": CID, "X-Naver-Client-Secret": CSEC}),
    ("https://openapi.naver.com/v1/search/kin.json",
     {"X-NCP-APIGW-API-KEY-ID": CID, "X-NCP-APIGW-API-KEY": CSEC}),
    ("https://naveropenapi.apigw.ntruss.com/v1/search/kin.json",
     {"X-NCP-APIGW-API-KEY-ID": CID, "X-NCP-APIGW-API-KEY": CSEC}),
]

working = None  # 성공한 (url, headers)
errors = []


def search(keyword):
    global working
    qs = urllib.parse.urlencode({"query": keyword, "display": DISPLAY, "sort": "sim"})
    combos = [working] if working else COMBOS
    for url, headers in combos:
        req = urllib.request.Request(f"{url}?{qs}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.load(res)
            if working is None:
                working = (url, headers)
                print(f"[인증 OK] {url} / 헤더 {list(headers)[0]}")
            return data.get("items", [])
        except urllib.error.HTTPError as e:
            body = e.read()[:200].decode("utf-8", "replace")
            errors.append(f"{url} → HTTP {e.code}: {body}")
        except Exception as e:
            errors.append(f"{url} → {type(e).__name__}: {e}")
    return None


def clean(s):
    return html.unescape(re.sub(r"</?b>", "", s)).strip()


def main():
    now = datetime.datetime.now(KST)
    lines = [f"# 지식iN 질문 조사 — {now:%Y-%m-%d %H:%M} (KST)", "",
             f"키워드: {', '.join(KEYWORDS)} / 키워드당 최대 {DISPLAY}건", ""]
    seen, total = set(), 0
    for kw in KEYWORDS:
        items = search(kw)
        if items is None:
            print("::error::지식iN API 호출 실패. 시도 내역:")
            for e in errors:
                print("  -", e)
            raise SystemExit(1)
        lines.append(f"## {kw} ({len(items)}건)")
        for it in items:
            link = it.get("link", "")
            if link in seen:
                continue
            seen.add(link)
            total += 1
            lines.append(f"- {clean(it.get('title',''))}  \n  {link}")
        lines.append("")
        print(f"[수집] {kw}: {len(items)}건")
    os.makedirs("research", exist_ok=True)
    path = f"research/지식인-{now:%Y%m%d-%H%M}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"저장: {path} (중복 제외 {total}건)")


if __name__ == "__main__":
    main()
