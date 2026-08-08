# 라이브 워드프레스의 발행·예약 글 전체 본문을 review/ 폴더로 내려받아 커밋한다.
# (클라우드 세션은 WP 키가 없어 직접 못 읽으므로, Actions에서 실행해 리포로 가져온다.)
# 산출물: review/post-{id}.md (본문 전체 + 메타), review/INDEX.md (지표 표)
import os, re, json, base64, html, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"


def wp(path):
    req = urllib.request.Request(
        API + path,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def text_of(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def main():
    os.makedirs("review", exist_ok=True)
    posts = []
    for status in ("publish", "future"):
        posts += wp(f"/posts?status={status}&per_page=100&context=edit"
                    "&_fields=id,title,content,excerpt,date,status,link,categories")
    posts.sort(key=lambda p: p["id"])

    rows = []
    for p in posts:
        raw = p["content"]["raw"]
        title = text_of(p["title"]["rendered"])
        body_txt = text_of(raw)
        chars = len(body_txt.replace("\n", "").replace(" ", ""))
        h2 = len(re.findall(r"<h2", raw))
        internal = len(re.findall(r'href="https://jaylog\.co\.kr/\?p=\d+"', raw))
        external = len(re.findall(r'href="https?://(?!jaylog\.co\.kr)', raw))
        imgs = re.findall(r"<img[^>]*>", raw)
        with_alt = sum(1 for i in imgs if re.search(r'alt="[^"]+"', i))
        tables = len(re.findall(r"<table", raw))
        lists = len(re.findall(r"<[uo]l", raw))
        ex = p["excerpt"]["raw"].strip()

        # 개별 파일로 본문 저장 (정독용)
        with open(f"review/post-{p['id']}.md", "w", encoding="utf-8") as f:
            f.write(f"# [{p['id']}] {title}\n\n")
            f.write(f"- status: {p['status']} / date: {p['date']} / link: {p['link']}\n")
            f.write(f"- 글자수(공백제외): {chars} / h2: {h2} / 표: {tables} / 리스트: {lists}\n")
            f.write(f"- 내부링크: {internal} / 외부링크: {external} / 이미지: {len(imgs)}(alt {with_alt})\n")
            f.write(f"- excerpt: {ex or '(비어있음)'}\n\n---\n\n")
            f.write(raw)

        rows.append((p["id"], p["status"], chars, h2, tables, lists,
                     internal, external, len(imgs), with_alt, bool(ex), title))

    with open("review/INDEX.md", "w", encoding="utf-8") as f:
        f.write("# 전체 글 지표 (자동 추출)\n\n")
        f.write("| id | 상태 | 글자 | h2 | 표 | 리스트 | 내부 | 외부 | 이미지(alt) | 요약 | 제목 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
        for (pid, st, ch, h2, tb, ls, inl, exl, im, al, ex, ti) in rows:
            f.write(f"| {pid} | {st} | {ch} | {h2} | {tb} | {ls} | {inl} | {exl} | "
                    f"{im}({al}) | {'O' if ex else 'X'} | {ti[:34]} |\n")
        f.write(f"\n총 {len(rows)}개 글\n")

    print(f"내보내기 완료: {len(rows)}개 글 → review/ 폴더")


if __name__ == "__main__":
    main()
