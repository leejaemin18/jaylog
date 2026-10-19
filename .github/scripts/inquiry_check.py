# 새 문의(블로그 댓글) 확인 (inquiry-check.yml).
# 지난 확인 이후 달린 댓글(승인 + 승인대기, 스팸 제외, 운영자 본인 댓글 제외)을 모아
#   review/inquiries-new.txt  — 이번 확인분만(매번 덮어씀, 없으면 '새 문의 없음')
#   review/inquiries-log.md   — 누적 기록
# 에 남기고, 마지막으로 본 댓글 id를 review/inquiry-state.json 에 저장한다.
# 처음 실행(상태 파일 없음)이면 최근 14일 댓글을 새 문의로 본다.
# ⚠️ 저장소가 공개이므로 댓글 작성자·내용은 파일에 쓰지 않는다(개수·글 제목·링크만).
import os, re, json, base64, html, datetime, urllib.request, urllib.error

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
STATE = "review/inquiry-state.json"
KST = datetime.timezone(datetime.timedelta(hours=9))


def wp(path):
    req = urllib.request.Request(API + path, headers={"Authorization": "Basic " + AUTH})
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def main():
    me = wp("/users/me?_fields=id")["id"]
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    last_id = state.get("last_id")
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S")

    found = {}
    max_seen = last_id or 0
    for status in ("approve", "hold"):
        try:
            rows = wp(f"/comments?status={status}&per_page=100&orderby=id&order=desc&context=edit"
                      "&_fields=id,post,author,author_name,date,content,link,status,parent")
        except urllib.error.HTTPError as e:
            print(f"::warning::{status} 댓글 조회 실패({e.code})")
            continue
        for c in rows:
            max_seen = max(max_seen, c["id"])
            if c["author"] == me:
                continue
            if last_id is not None and c["id"] <= last_id:
                continue
            if last_id is None and c["date"] < since:
                continue
            found[c["id"]] = c

    titles = {}
    for pid in {c["post"] for c in found.values()}:
        try:
            titles[pid] = plain(wp(f"/posts/{pid}?_fields=title")["title"]["rendered"])
        except Exception:
            try:
                titles[pid] = plain(wp(f"/pages/{pid}?_fields=title")["title"]["rendered"])
            except Exception:
                titles[pid] = f"id {pid}"

    now = datetime.datetime.now(KST)
    lines = []
    for c in sorted(found.values(), key=lambda x: x["id"]):
        st = "승인대기" if c["status"] == "hold" else "공개"
        kind = "답글" if c.get("parent") else "새 댓글"
        # 저장소가 공개라 작성자·내용은 남기지 않는다(승인대기 댓글 노출 방지). 내용은 링크/WP 관리자에서 확인.
        lines.append(f"- [{st}·{kind}] {c['date'][:16].replace('T', ' ')} · 글: {titles.get(c['post'])}\n"
                     f"  링크: {c['link']}")

    os.makedirs("review", exist_ok=True)
    head = f"# 문의 확인 {now:%Y-%m-%d %H:%M} KST — 새 댓글 {len(lines)}개"
    with open("review/inquiries-new.txt", "w", encoding="utf-8") as f:
        f.write(head + "\n" + ("\n".join(lines) if lines else "새 문의 없음") + "\n")
    if lines:
        with open("review/inquiries-log.md", "a", encoding="utf-8") as f:
            f.write("\n" + head + "\n" + "\n".join(lines) + "\n")

    state["last_id"] = max_seen
    state["checked_at"] = now.isoformat(timespec="minutes")
    with open(STATE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    print(open("review/inquiries-new.txt", encoding="utf-8").read())


if __name__ == "__main__":
    main()
