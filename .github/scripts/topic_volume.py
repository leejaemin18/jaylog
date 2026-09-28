# 주제 후보 키워드별 '검색 수요'를 숫자로 비교하는 조사 스크립트 (topic-volume.yml).
# 지표:
#   kin/blog/cafe — 네이버 검색 API의 total(전체 결과 수): 질문·글이 얼마나 쌓였나(누적 관심도)
#   datalab       — 네이버 데이터랩 검색어 트렌드(최근 12개월 합계)를 기준어('해외직구') 대비 %로 환산:
#                   실제 사람들이 검색창에 친 양. 앱에 데이터랩 권한이 없으면 '-'로 둔다.
# 입력: KEYWORDS(쉼표 구분). 비어 있으면 research/topic-keywords.txt(한 줄에 하나) 사용.
import os, json, datetime, urllib.parse, urllib.request

CID = os.environ["NAVER_CLIENT_ID"].strip()
CSEC = os.environ["NAVER_CLIENT_SECRET"].strip()
KST = datetime.timezone(datetime.timedelta(hours=9))
ANCHOR = "해외직구"
HDR = {"X-Naver-Client-Id": CID, "X-Naver-Client-Secret": CSEC}


def load_keywords():
    raw = os.environ.get("KEYWORDS", "").strip()
    if raw:
        kws = [k.strip() for k in raw.split(",")]
    else:
        with open("research/topic-keywords.txt", encoding="utf-8") as f:
            kws = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    out = []
    for k in kws:
        if k and k not in out:
            out.append(k)
    return out


def total(kind, kw):
    qs = urllib.parse.urlencode({"query": kw, "display": 1})
    req = urllib.request.Request(f"https://openapi.naver.com/v1/search/{kind}.json?{qs}", headers=HDR)
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            return int(json.load(res).get("total", 0))
    except Exception as e:
        print(f"::warning::{kind} 실패({kw}): {e}")
        return None


def datalab(keywords):
    """기준어 + 4개씩 묶어 요청 → 각 키워드 12개월 합 / 기준어 12개월 합 × 100."""
    end = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)   # 지난달 말
    start = (end.replace(day=1) - datetime.timedelta(days=330)).replace(day=1)  # 약 12개월 전
    result = {}
    for i in range(0, len(keywords), 4):
        batch = [k for k in keywords[i:i + 4] if k != ANCHOR]
        groups = [{"groupName": ANCHOR, "keywords": [ANCHOR]}] + \
                 [{"groupName": k, "keywords": [k]} for k in batch]
        body = json.dumps({"startDate": str(start), "endDate": str(end), "timeUnit": "month",
                           "keywordGroups": groups}).encode()
        req = urllib.request.Request("https://openapi.naver.com/v1/datalab/search", data=body,
                                     headers={**HDR, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                data = json.load(res)
        except urllib.error.HTTPError as e:
            print(f"::warning::데이터랩 사용 불가(HTTP {e.code}) — 검색량 지수 생략: {e.read()[:150]}")
            return None
        except Exception as e:
            print(f"::warning::데이터랩 실패: {e}")
            return None
        sums = {r["title"]: sum(d["ratio"] for d in r["data"]) for r in data.get("results", [])}
        base = sums.get(ANCHOR) or 0
        for k in batch:
            result[k] = round(sums.get(k, 0) / base * 100, 2) if base else 0.0
    result[ANCHOR] = 100.0
    return result


def main():
    kws = load_keywords()
    rows = []
    for kw in kws:
        r = {"kw": kw, "kin": total("kin", kw), "blog": total("blog", kw), "cafe": total("cafearticle", kw)}
        rows.append(r)
        print(f"[측정] {kw}: kin={r['kin']} blog={r['blog']} cafe={r['cafe']}")
    dl = datalab(kws)
    for r in rows:
        r["dl"] = dl.get(r["kw"]) if dl else None

    # 정렬: 데이터랩 지수가 있으면 그걸로, 없으면 지식iN 질문 수로
    key = (lambda r: (r["dl"] or 0)) if dl else (lambda r: (r["kin"] or 0))
    rows.sort(key=key, reverse=True)

    now = datetime.datetime.now(KST)
    lines = [f"# 주제 검색 수요 조사 — {now:%Y-%m-%d %H:%M} (KST)", "",
             f"키워드 {len(rows)}개 · 정렬 기준: {'데이터랩 검색량 지수(기준어 해외직구=100, 최근 12개월)' if dl else '지식iN 질문 수(데이터랩 권한 없음)'}",
             "", "- 데이터랩 지수: 실제 검색창 검색량 (기준어 대비 %)",
             "- 지식iN/블로그/카페: 네이버 검색 결과 누적 건수 (질문·글이 얼마나 쌓였나)", "",
             "| 순위 | 키워드 | 데이터랩 지수 | 지식iN 질문 | 블로그 | 카페 |", "|---|---|---|---|---|---|"]
    f = lambda v: "-" if v is None else f"{v:,}"
    for i, r in enumerate(rows, 1):
        lines.append(f"| {i} | {r['kw']} | {'-' if r['dl'] is None else r['dl']} | {f(r['kin'])} | {f(r['blog'])} | {f(r['cafe'])} |")
    os.makedirs("research", exist_ok=True)
    path = f"research/검색량-{now:%Y%m%d-%H%M}.md"
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print(f"저장: {path}")


if __name__ == "__main__":
    main()
