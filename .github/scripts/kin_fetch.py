# 지식iN 질문 1건의 '본문'을 러너에서 가져와 research/에 저장한다(질문 정확 분석용).
# 사용: 환경변수 QDOCID(필수), QD1ID/QDIRID(선택).
import os, re, html, urllib.parse, urllib.request

DOCID = os.environ["QDOCID"].strip()
D1 = os.environ.get("QD1ID", "").strip()
DIR = os.environ.get("QDIRID", "").strip()
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0 Safari/537.36")


def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko-KR,ko"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        return f"__ERR__ {e}"


def strip_tags(s):
    s = re.sub(r"(?is)<script.*?</script>", " ", s)
    s = re.sub(r"(?is)<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    return html.unescape(re.sub(r"[ \t\r\n]{2,}", " ", s)).strip()


def field(h, prop):
    m = re.search(rf'<meta property="{prop}" content="([^"]*)"', h) or \
        re.search(rf'<meta name="{prop}" content="([^"]*)"', h)
    return html.unescape(m.group(1)).strip() if m else ""


def main():
    params = {k: v for k, v in [("d1id", D1), ("dirId", DIR), ("docId", DOCID)] if v}
    murl = "https://m.kin.naver.com/mobile/qna/detail.naver?" + urllib.parse.urlencode(params)
    h = get(murl)
    out = [f"# 지식iN 질문 원문 — docId {DOCID}", f"URL: {murl}", ""]
    if h.startswith("__ERR__") or not h:
        out.append(f"가져오기 실패: {h}")
    else:
        out.append(f"제목(og:title): {field(h,'og:title')}")
        out.append(f"요약(og:description): {field(h,'og:description')}")
        out.append("")
        # 질문 영역 텍스트 추출 시도(여러 컨테이너 후보)
        body = ""
        for pat in [r'<div[^>]*class="[^"]*(?:questionDetail|q_content|answerArea|se-main-container|endContent)[^"]*"[^>]*>(.*?)</div>\s*(?:<div|<section|$)']:
            m = re.search(pat, h, re.S | re.I)
            if m:
                body = strip_tags(m.group(1))
                if len(body) > 20:
                    break
        if not body:
            # 폴백: 전체에서 본문 텍스트 크게 한 덩어리
            body = strip_tags(h)[:2000]
        out.append("본문 추출:")
        out.append(body[:2500])
    os.makedirs("research", exist_ok=True)
    path = f"research/지식인-질문-{DOCID}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out)[:1500])
    print(f"\n저장: {path}")


if __name__ == "__main__":
    main()
