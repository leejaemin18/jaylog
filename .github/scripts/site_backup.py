# 사이트 전체 백업 (site-backup.yml) — 서버 이전·해지 전 자료 보존용.
# backup/content/ : 글·페이지(초안·비공개 포함, 원문 raw+렌더 HTML), 카테고리, 태그, 메뉴, 사이트 설정,
#                   댓글(작성자 이메일·IP·브라우저 정보는 제외), 미디어 목록
# backup/media/   : 미디어 라이브러리 원본 파일 전부
# (사이트 전체 HTML 사본은 워크플로의 wget 단계가 backup/mirror/ 에 만든다)
# 결과는 저장소에 커밋하지 않는다(댓글 등 개인정보) — 워크플로 아티팩트로만 내려받는다.
import os, json, base64, urllib.request, urllib.error, urllib.parse

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
SITE = "https://jaylog.co.kr"
API = SITE + "/wp-json/wp/v2"
OUT = "backup"


def get(path, raw=False):
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url, headers={"Authorization": "Basic " + AUTH,
                                               "User-Agent": "jaylog-backup"})
    with urllib.request.urlopen(req, timeout=120) as res:
        data = res.read()
        return data if raw else (json.loads(data), res.headers)


def get_all(path):
    out, page = [], 1
    sep = "&" if "?" in path else "?"
    while True:
        try:
            batch, hdr = get(f"{path}{sep}per_page=100&page={page}")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                break
            raise
        out += batch
        if page >= int(hdr.get("X-WP-TotalPages", "1") or 1):
            break
        page += 1
    return out


def save(name, data):
    os.makedirs(f"{OUT}/content", exist_ok=True)
    with open(f"{OUT}/content/{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"  {name}: {len(data) if isinstance(data, list) else 'ok'}")


def main():
    print("콘텐츠 내보내기")
    statuses = "publish,future,draft,pending,private"
    save("posts", get_all(f"/posts?status={statuses}&context=edit"))
    save("pages", get_all(f"/pages?status={statuses}&context=edit"))
    save("categories", get_all("/categories?context=edit"))
    save("tags", get_all("/tags?context=edit"))
    media = get_all("/media?context=edit")
    save("media", media)

    comments = []
    for st in ("approve", "hold"):
        try:
            comments += get_all(f"/comments?status={st}&context=edit")
        except urllib.error.HTTPError as e:
            print(f"::warning::댓글({st}) 조회 실패 {e.code}")
    for c in comments:  # 개인정보 제외
        for k in ("author_email", "author_ip", "author_user_agent"):
            c.pop(k, None)
    save("comments", comments)

    for name, path in (("settings", "/settings"), ("menus", "/menus?context=edit"),
                       ("menu-items", "/menu-items?context=edit"), ("me", "/users/me?context=edit")):
        try:
            data, _ = get(path)
            if name == "me":
                data = {k: data.get(k) for k in ("id", "name", "slug", "description", "url")}
            if name == "settings":
                data.pop("email", None)
            save(name, data)
        except Exception as e:
            print(f"::warning::{name} 실패 — {e}")

    print("미디어 원본 받기")
    os.makedirs(f"{OUT}/media", exist_ok=True)
    ok = fail = 0
    for m in media:
        src = m.get("source_url", "")
        if not src:
            continue
        rel = urllib.parse.urlparse(src).path.split("/wp-content/uploads/")[-1]
        dest = os.path.join(OUT, "media", rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            with open(dest, "wb") as f:
                f.write(get(src, raw=True))
            ok += 1
        except Exception as e:
            fail += 1
            print(f"::warning::미디어 실패 {src} — {e}")
    print(f"미디어: 성공 {ok} / 실패 {fail}")


if __name__ == "__main__":
    main()
