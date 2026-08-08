# 애드센스 재점검용 사이트 감사 (blog-command: site-audit).
# 페이지(소개·문의·개인정보처리방침·이용약관·계산기 등) 목록·글자수·필수조항 포함 여부,
# 저자(claude) 소개(bio) 상태, 발행/예약 글 수를 review/site-audit.txt 에 기록·커밋.
import os, re, json, base64, html, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"


def wp(path):
    req = urllib.request.Request(
        API + path, headers={"Authorization": "Basic " + AUTH,
                             "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def text_of(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def main():
    os.makedirs("review", exist_ok=True)
    out = []
    # 페이지 전수
    pages = wp("/pages?status=publish,draft&per_page=100&context=edit"
               "&_fields=id,title,slug,status,content,link")
    out.append("=== 페이지 목록 ===")
    for p in sorted(pages, key=lambda x: x["id"]):
        raw = p["content"]["raw"]
        chars = len(text_of(raw).replace("\n", "").replace(" ", ""))
        kw = []
        low = raw.lower()
        if "개인정보" in raw: kw.append("개인정보")
        if "쿠키" in raw or "cookie" in low: kw.append("쿠키")
        if "adsense" in low or "애드센스" in raw or "광고" in raw: kw.append("광고/애드센스")
        if "제3자" in raw or "제 3자" in raw or "third" in low: kw.append("제3자")
        title = text_of(p["title"]["rendered"])
        out.append(f"[{p['id']}] {title} | slug={p['slug']} | {p['status']} | "
                   f"{chars}자 | 조항:{','.join(kw) or '-'} | {p['link']}")
    # 저자 bio
    out.append("\n=== 저자(claude) ===")
    try:
        me = wp("/users/me?context=edit&_fields=id,name,description,url")
        out.append(f"id={me['id']} name={me['name']} "
                   f"bio={'(비어있음)' if not me.get('description') else me['description'][:120]}")
    except Exception as e:
        out.append(f"저자 조회 실패: {e}")
    # 글 수
    pub = wp("/posts?status=publish&per_page=100&_fields=id")
    fut = wp("/posts?status=future&per_page=100&_fields=id")
    drf = wp("/posts?status=draft&per_page=100&_fields=id")
    out.append(f"\n=== 글 수 === 발행 {len(pub)} / 예약 {len(fut)} / 초안 {len(drf)}")

    txt = "\n".join(out)
    print(txt)
    with open("review/site-audit.txt", "w", encoding="utf-8") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
