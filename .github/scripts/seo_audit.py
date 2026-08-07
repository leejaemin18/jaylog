# 전 글 SEO 점검 + 안전한 자동 수정 (blog-command의 seo-audit 명령).
# 점검: 외부링크·내부링크수·이미지/alt·요약(excerpt)·H2수·글자수
# 자동수정: 요약(excerpt)이 비어 있으면 첫 문단에서 생성해 채움 (Rank Math 메타설명 폴백으로 쓰임)
import os, re, json, base64, html, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def text_of(htmlstr):
    return html.unescape(re.sub(r"<[^>]+>", "", htmlstr)).strip()


def main():
    posts = []
    for status in ("publish", "future"):
        posts += wp(f"/posts?status={status}&per_page=100&context=edit&_fields=id,title,content,excerpt")
    print(f"{'id':>4} | 외부 | 내부 | 이미지(alt) | H2 | 글자수 | 요약 | 제목")
    print("-" * 90)
    fixed = 0
    for p in sorted(posts, key=lambda x: x["id"]):
        raw = p["content"]["raw"]
        rendered = p["content"]["rendered"]
        title = text_of(p["title"]["rendered"])[:24]
        # 외부 링크(관세청)
        outb = "O" if "customs.go.kr" in raw and "<a href=\"https://www.customs.go.kr" in raw else "X"
        # 내부 링크 수 (jaylog 본문 링크)
        internal = len(re.findall(r'href="https://jaylog\.co\.kr/\?p=\d+"', raw)) + len(re.findall(r'href="/[a-z]', raw))
        # 이미지 / alt 유무
        imgs = re.findall(r"<img[^>]*>", raw)
        with_alt = sum(1 for i in imgs if re.search(r'alt="[^"]+"', i))
        img_str = f"{len(imgs)}({with_alt})"
        # H2 개수
        h2 = len(re.findall(r"<h2", raw))
        # 글자수
        chars = len(text_of(raw).replace("\n", ""))
        # 요약(excerpt)
        ex_raw = p["excerpt"]["raw"].strip()
        ex_state = "있음"
        if not ex_raw:
            # 첫 문단 텍스트로 요약 생성
            m = re.search(r"<p>(.*?)</p>", raw, re.S)
            first = text_of(m.group(1)) if m else text_of(raw)
            desc = first[:150].rsplit(" ", 1)[0] if len(first) > 150 else first
            if desc:
                wp(f"/posts/{p['id']}", "POST", {"excerpt": desc})
                ex_state = "채움✔"
                fixed += 1
        print(f"{p['id']:>4} |  {outb}   |  {internal:>2}  |   {img_str:>6}   | {h2:>2} | {chars:>5} | {ex_state:>4} | {title}")
    print("-" * 90)
    print(f"요약 자동 생성: {fixed}건 / 전체 {len(posts)}건")
    print("※ 외부=관세청 링크, 이미지(alt)=이미지수(alt있는수), 내부=본문 내부링크 수")


if __name__ == "__main__":
    main()
