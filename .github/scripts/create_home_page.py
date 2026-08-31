# 제이로그 대문(홈) 랜딩 페이지를 생성/갱신하고, 정적 홈페이지로 지정한다 (blog-command: create-home-page).
# 밋밋한 기본 글목록 대신 히어로+도구카드+상황별 바로가기+주제별 글+신뢰배지로 첫인상을 강화(애드센스·체류시간).
# 정적 프런트 지정은 권한이 있으면 /settings로 자동 적용, 없으면 안내만 남긴다.
import os, json, base64, urllib.request, urllib.error

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
BASE = "https://jaylog.co.kr/wp-json/wp/v2"
SLUG = "home"

CONTENT = open("assets/home.html", encoding="utf-8").read()


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


def main():
    existing = wp(f"/pages?slug={SLUG}&status=publish,draft&_fields=id")
    payload = {"title": "제이로그 — 해외직구·통관 가이드",
               "slug": SLUG, "status": "publish", "content": CONTENT}
    if existing:
        pid = existing[0]["id"]
        r = wp(f"/pages/{pid}", "POST", payload)
        print(f"♻️ 홈 페이지 갱신: id {pid}")
    else:
        r = wp("/pages", "POST", payload)
        print(f"✅ 홈 페이지 생성: id {r['id']}")
    pid = r["id"]
    link = r["link"]

    # 글 목록(블로그) 페이지 확보 — 정적 홈으로 바꾸면 전체 글 보기 경로가 필요
    blog = wp("/pages?slug=blog&status=publish,draft&_fields=id")
    if blog:
        blog_id = blog[0]["id"]
        print(f"블로그 목록 페이지 존재: id {blog_id}")
    else:
        b = wp("/pages", "POST", {"title": "블로그", "slug": "blog", "status": "publish", "content": ""})
        blog_id = b["id"]
        print(f"✅ 블로그 목록 페이지 생성: id {blog_id}")

    # 정적 프런트 + 글 목록 페이지 지정 (admin 권한 필요)
    front_ok = False
    try:
        wp("/settings", "POST", {"show_on_front": "page", "page_on_front": pid, "page_for_posts": blog_id})
        front_ok = True
        print(f"✅ 정적 홈페이지 지정 완료 (홈={pid}, 글목록={blog_id})")
    except urllib.error.HTTPError as e:
        print(f"::warning::정적 홈페이지 자동 지정 실패({e.code}) — WP 관리자 > 설정 > 읽기 에서 "
              f"홈페이지='제이로그 — 해외직구·통관 가이드', 글 페이지='블로그'로 직접 지정하세요.")
    except Exception as e:
        print(f"::warning::정적 홈페이지 자동 지정 실패 — {e}")

    os.makedirs("review", exist_ok=True)
    with open("review/home-page.txt", "w", encoding="utf-8") as f:
        f.write(f"id={pid}\nlink={link}\nfront_set={front_ok}\n")
    print(f"링크: {link}")


if __name__ == "__main__":
    main()
