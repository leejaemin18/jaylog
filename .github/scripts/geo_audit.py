# GEO 적용 현황 점검 (blog-command: geo-audit).
# 발행·예약 글 전체를 훑어 각 글에 '한눈 요약'(geo-summary)과 FAQ(FAQPage JSON-LD)가
# 들어가 있는지 확인하고 review/geo-audit.txt 에 기록. 백필 누락 검증 + 정기 건강검진용.
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


def text_title(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def main():
    os.makedirs("review", exist_ok=True)
    posts = []
    for status in ("publish", "future"):
        posts += wp(f"/posts?status={status}&per_page=100&context=edit"
                    f"&_fields=id,title,status,content")
    posts.sort(key=lambda p: p["id"])

    out, missing_sum, missing_faq = [], [], []
    out.append(f"=== GEO 점검: 총 {len(posts)}개 (발행+예약) ===")
    out.append("id  | 요약 | FAQ | 상태 | 제목")
    for p in posts:
        raw = p["content"]["raw"]
        s = "geo-summary" in raw
        f = "FAQPage" in raw
        if not s:
            missing_sum.append(p["id"])
        if not f:
            missing_faq.append(p["id"])
        out.append(f"{p['id']:>4} |  {'O' if s else 'X'}  |  {'O' if f else 'X'}  | "
                   f"{p['status']:<7} | {text_title(p['title']['rendered'])[:44]}")

    out.append("")
    out.append(f"요약 없음({len(missing_sum)}): {missing_sum or '-'}")
    out.append(f"FAQ 없음({len(missing_faq)}): {missing_faq or '-'}")
    ok = len(posts) - len(set(missing_sum) | set(missing_faq))
    out.append(f"GEO 완비: {ok}/{len(posts)}개")

    txt = "\n".join(out)
    print(txt)
    with open("review/geo-audit.txt", "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    main()
