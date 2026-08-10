# 라이브 글 AI 티 점검 (blog-command: humanize-audit).
# 발행·예약 글 본문을 humanize 스코어러로 훑어 AI 티가 강한 글을 review/humanize-audit.txt에 기록.
# 어떤 글부터 /humanize-korean 으로 손볼지 우선순위를 잡는 용도.
import os, re, json, base64, urllib.request, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from humanize_gate import strip_html, score  # 동일 스코어러 재사용

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


def title_of(h):
    import html
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def main():
    os.makedirs("review", exist_ok=True)
    posts = []
    for status in ("publish", "future"):
        posts += wp(f"/posts?status={status}&per_page=100&context=edit&_fields=id,title,content")
    rows = []
    for p in posts:
        try:
            plain = strip_html(p["content"]["raw"])
            m = score(plain)
            lt = m["lexical_tells"]
            flag = (lt["s1_total"] >= 1 or lt["mechanical_list"] >= 3
                    or lt["s2_total"] >= 6 or m.get("route_hint") == "heavy")
            rows.append((p["id"], lt["s1_total"], lt["s2_total"], lt["mechanical_list"],
                         m.get("route_hint", "?"), flag, title_of(p["title"]["rendered"])))
        except Exception as e:
            rows.append((p["id"], -1, -1, -1, "err", True, f"(스코어 실패: {e})"))
    # AI 티 강한 순 정렬(S1 우선, 그다음 S2)
    rows.sort(key=lambda r: (r[1], r[2], r[3]), reverse=True)

    out = [f"=== AI 티 점검: 총 {len(posts)}개 (발행+예약) ===",
           "id  | S1 | S2 | 병렬 | route | 손볼것 | 제목"]
    flagged = 0
    for pid, s1, s2, mech, hint, flag, title in rows:
        if flag:
            flagged += 1
        out.append(f"{pid:>4} | {s1:>2} | {s2:>2} |  {mech:>2}  | {hint:<8} | "
                   f"{'⚠️' if flag else '  '}  | {title[:40]}")
    out.append(f"\n윤문 권장(플래그): {flagged}/{len(posts)}개")
    out.append("S1=상투구(무조건 제거) · S2=번역투(반복 시) · 병렬=첫째·둘째·셋째")

    txt = "\n".join(out)
    print(txt)
    with open("review/humanize-audit.txt", "w", encoding="utf-8") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
