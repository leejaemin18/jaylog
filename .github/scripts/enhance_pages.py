# 애드센스 재점검 보강 (blog-command: enhance-pages).
# 1) 소개(About) 페이지를 pages/about.html 내용으로 갱신 (E-E-A-T 자격 서사).
# 2) 저자(claude=/users/me) bio(description) 설정 — 익명 저자 감점 방지.
# 3) 문의/면책 페이지 원문을 review/pages-contact-disclaimer.txt로 덤프(수익성 문구 점검용).
import os, re, json, base64, html, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"

ABOUT_SLUG = "about"
BIO = ("해외직구·통관 정보 블로그 '제이로그'를 운영합니다. 복잡한 통관·관세 규정을 "
       "50대 독자의 눈높이에서 쉽게 풀어 쓰고, 규정과 수치는 관세청 등 공식 자료로 "
       "확인해 2026년 기준으로 정확하게 전달하려 합니다.")


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def text_of(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def main():
    # 1) About 갱신
    about_html = open("pages/about.html", encoding="utf-8").read().strip()
    pages = wp(f"/pages?slug={ABOUT_SLUG}&status=publish,draft&_fields=id")
    if pages:
        pid = pages[0]["id"]
        r = wp(f"/pages/{pid}", "POST", {"content": about_html})
        n = len(text_of(about_html).replace("\n", "").replace(" ", ""))
        print(f"✅ 소개 페이지 갱신: id {pid} ({n}자)")
    else:
        print("::warning::about 슬러그 페이지를 찾지 못함 — 수동 확인 필요")

    # 2) 저자 bio
    try:
        me = wp("/users/me?context=edit&_fields=id,name")
        wp(f"/users/{me['id']}", "POST", {"description": BIO})
        print(f"✅ 저자 bio 설정: id {me['id']} ({me['name']})")
    except Exception as e:
        print(f"::warning::저자 bio 설정 실패 — {e}")

    # 3) 문의/면책 덤프
    os.makedirs("review", exist_ok=True)
    dump = []
    for slug in ("contact", "disclaimer"):
        ps = wp(f"/pages?slug={slug}&context=edit&_fields=id,title,content")
        if ps:
            dump.append(f"=== [{ps[0]['id']}] {text_of(ps[0]['title']['rendered'])} (slug={slug}) ===")
            dump.append(ps[0]["content"]["raw"])
            dump.append("")
    with open("review/pages-contact-disclaimer.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(dump))
    print("문의/면책 원문 덤프 → review/pages-contact-disclaimer.txt")


if __name__ == "__main__":
    main()
