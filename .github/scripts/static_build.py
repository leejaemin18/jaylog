# 무료 정적 사이트 만들기 (static-build.yml) — 워드프레스 서버를 끄기 전 '준비'용.
#
#   python3 static_build.py prepare   : 글 번호→주소 표, 사이트맵·robots·ads.txt, wget 시작 주소 목록
#   (워크플로가 wget으로 사이트 전체를 build/out/ 에 받는다)
#   python3 static_build.py finish    : 뒷정리(파일명 보정·댓글창 제거·404 페이지·?p= 이동 함수) + 점검 보고서
#
# 결과물 build/out/ 은 Cloudflare Pages에 그대로 올릴 수 있는 형태.
# ?p=123 같은 옛 주소는 정적 호스팅이 처리 못 하므로 build/functions/index.js(Pages Function)가 301로 넘긴다.
import os, sys, re, json, base64, shutil, urllib.request, urllib.error, urllib.parse

SITE = "https://jaylog.co.kr"
API = SITE + "/wp-json/wp/v2"
UA = "Mozilla/5.0 (compatible; jaylog-static-bot/1.0)"  # 'bot' 표기 → 방문자 통계에서 빠지게
BUILD = "build"
OUT = f"{BUILD}/out"
REPORT = "review/static-build.txt"
PW = os.environ.get("WP_APP_PASSWORD", "")
AUTH = base64.b64encode(f"claude:{PW}".encode()).decode() if PW else ""


def fetch(url, raw=False):
    h = {"User-Agent": UA}
    if AUTH and url.startswith(API):
        h["Authorization"] = "Basic " + AUTH
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        data = r.read()
        return data if raw else (json.loads(data), r.headers)


def get_all(path):
    out, page = [], 1
    while True:
        try:
            batch, hdr = fetch(f"{API}{path}&per_page=100&page={page}")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                break
            raise
        out += batch
        if page >= int(hdr.get("X-WP-TotalPages", "1") or 1):
            break
        page += 1
    return out


def save_raw(rel, data):
    dest = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dest) or OUT, exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)


def prepare():
    os.makedirs(OUT, exist_ok=True)
    items = []
    for kind in ("posts", "pages"):
        for it in get_all(f"/{kind}?status=publish&_fields=id,link,type"):
            items.append({"id": it["id"], "type": it["type"], "link": it["link"]})
    json.dump(items, open(f"{BUILD}/items.json", "w"), ensure_ascii=False, indent=1)
    print(f"공개 글 {sum(i['type']=='post' for i in items)}개 · 페이지 {sum(i['type']=='page' for i in items)}개")

    urls = {SITE + "/"} | {i["link"] for i in items}
    # 사이트맵(검색엔진용)은 링크로 안 걸려 있어 wget이 못 찾으므로 따로 받는다
    sitemaps = []
    try:
        idx = fetch(SITE + "/sitemap_index.xml", raw=True)
        save_raw("sitemap_index.xml", idx)
        sitemaps = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", idx.decode("utf-8", "replace"))
    except Exception as e:
        print(f"::warning::sitemap_index.xml 실패 — {e}")
    for sm in sitemaps:
        try:
            data = fetch(sm, raw=True)
            save_raw(urllib.parse.urlparse(sm).path.lstrip("/"), data)
            urls |= set(re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", data.decode("utf-8", "replace")))
        except Exception as e:
            print(f"::warning::사이트맵 실패 {sm} — {e}")
    for extra in ("robots.txt", "ads.txt", "main-sitemap.xsl"):
        try:
            save_raw(extra, fetch(f"{SITE}/{extra}", raw=True))
        except Exception:
            pass
    urls = sorted(u for u in urls if u.startswith(SITE) and not u.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")))
    open(f"{BUILD}/urls.txt", "w").write("\n".join(urls) + "\n")
    print(f"사이트맵 {len(sitemaps)}개 · 시작 주소 {len(urls)}개")


COMMENT_FORM = re.compile(r'<div id="respond".*?<!-- #respond -->', re.S)


def finish():
    items = json.load(open(f"{BUILD}/items.json"))
    fixed_assets = removed_forms = 0
    for root, _, files in os.walk(OUT):
        for fn in files:
            p = os.path.join(root, fn)
            # style.css?ver=1 → wget 파일명 style.css@ver=1.css. 절대주소(?ver=)로 부르는 곳도 열리게 원래 이름 사본
            if "@" in fn and not fn.endswith(".html"):
                base = os.path.join(root, fn.split("@", 1)[0])
                if os.path.splitext(base)[1] and not os.path.exists(base):
                    shutil.copyfile(p, base)
                    fixed_assets += 1
            # 댓글 작성창은 정적 사이트에서 동작하지 않으므로 뺀다(기존 댓글 표시는 유지)
            if fn.endswith(".html"):
                s = open(p, encoding="utf-8", errors="surrogateescape").read()
                s2, n = COMMENT_FORM.subn("", s)
                if n:
                    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s2)
                    removed_forms += n

    # 404 페이지
    try:
        fetch(SITE + "/no-such-page-jaylog-static/", raw=True)
    except urllib.error.HTTPError as e:
        html = e.read().decode("utf-8", "replace").replace(SITE + "/", "/")
        open(f"{OUT}/404.html", "w", encoding="utf-8").write(html)
    except Exception as e:
        print(f"::warning::404 페이지 실패 — {e}")

    # ?p=123 / ?page_id=123 → 글 주소로 301 (지식iN 답변·내부링크가 이 형태를 많이 씀)
    mp = {str(i["id"]): urllib.parse.urlparse(i["link"]).path for i in items}
    os.makedirs(f"{BUILD}/functions", exist_ok=True)
    open(f"{BUILD}/functions/index.js", "w", encoding="utf-8").write(
        "// 자동 생성(static_build.py) — 옛 주소 ?p=글번호 를 글 주소로 301 이동\n"
        f"const MAP = {json.dumps(mp, ensure_ascii=False)};\n"
        "export async function onRequest(context) {\n"
        "  const url = new URL(context.request.url);\n"
        "  const id = url.searchParams.get('p') || url.searchParams.get('page_id');\n"
        "  if (id && MAP[id]) return Response.redirect(url.origin + MAP[id], 301);\n"
        "  return context.next();\n"
        "}\n")

    # 점검: 공개 글·페이지가 전부 파일로 있는지
    missing = []
    for i in items:
        path = urllib.parse.unquote(urllib.parse.urlparse(i["link"]).path).strip("/")
        f = os.path.join(OUT, path, "index.html") if path else os.path.join(OUT, "index.html")
        if not os.path.exists(f):
            missing.append(f"{i['id']} {i['link']}")
    nfiles = sum(len(f) for _, _, f in os.walk(OUT))
    nhtml = sum(1 for _, _, fs in os.walk(OUT) for f in fs if f.endswith(".html"))
    size = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(OUT) for f in fs)
    big = [os.path.join(r, f) for r, _, fs in os.walk(OUT) for f in fs
           if os.path.getsize(os.path.join(r, f)) > 25 * 1024 * 1024]
    leftover = sum(1 for r, _, fs in os.walk(OUT) for f in fs if f.endswith(".html")
                   and "jaylog.co.kr/wp-content/" in open(os.path.join(r, f), errors="ignore").read())

    lines = [
        "# 무료 정적 사이트 빌드 점검",
        f"공개 글·페이지: {len(items)}개 / 빠진 것: {len(missing)}개",
        f"전체 파일: {nfiles}개 (Cloudflare Pages 한도 20,000) / HTML: {nhtml}개",
        f"전체 용량: {size/1024/1024:.1f}MB / 25MB 넘는 파일: {len(big)}개 (한도 25MB)",
        f"?ver= 자산 사본: {fixed_assets}개 / 댓글 작성창 제거: {removed_forms}곳",
        f"이미지를 아직 옛 서버 주소로 부르는 HTML: {leftover}개",
        f"404 페이지: {'있음' if os.path.exists(OUT + '/404.html') else '없음'}",
        f"?p= 이동 표: {len(mp)}개",
        "",
        "## 빠진 글·페이지",
        *(missing or ["없음"]),
        *(["", "## 25MB 넘는 파일", *big] if big else []),
    ]
    os.makedirs("review", exist_ok=True)
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[:9]))


if __name__ == "__main__":
    {"prepare": prepare, "finish": finish}[sys.argv[1]]()
