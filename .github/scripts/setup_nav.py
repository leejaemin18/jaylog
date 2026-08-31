# 헤더 정리 (blog-command: setup-nav).
# 1) 사이트 제목/태그라인을 짧고 깔끔하게.
# 2) 전용 메인 메뉴 생성 → 홈·진단·계산기·블로그·소개·문의 만 노출(긴 페이지 제목 난립 제거).
# 3) 법적 페이지(개인정보·DMCA·면책)는 푸터 메뉴로(있으면).
# 멱등: 같은 이름의 메뉴가 있으면 항목을 비우고 다시 채운다.
import os, json, base64, urllib.request, urllib.error

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
BASE = "https://jaylog.co.kr/wp-json/wp/v2"


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        BASE + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        body = res.read()
        return json.loads(body) if body else None


def page_id(slug):
    r = wp(f"/pages?slug={slug}&status=publish,draft&_fields=id")
    return r[0]["id"] if r else None


def ensure_menu(name):
    menus = wp("/menus?per_page=100&_fields=id,name")
    for m in menus or []:
        if m.get("name") == name:
            # 기존 항목 비우기
            items = wp(f"/menu-items?menus={m['id']}&per_page=100&_fields=id")
            for it in items or []:
                try:
                    wp(f"/menu-items/{it['id']}?force=true", "DELETE")
                except Exception as e:
                    print(f"  항목 삭제 실패 {it['id']}: {e}")
            return m["id"]
    m = wp("/menus", "POST", {"name": name})
    return m["id"]


def add_page_item(menu_id, title, pid, order):
    if not pid:
        return
    wp("/menu-items", "POST", {
        "title": title, "menus": menu_id, "status": "publish",
        "type": "post_type", "object": "page", "object_id": pid, "menu_order": order})
    print(f"  + {title} (page {pid})")


def add_url_item(menu_id, title, url, order):
    wp("/menu-items", "POST", {
        "title": title, "menus": menu_id, "status": "publish",
        "type": "custom", "url": url, "menu_order": order})
    print(f"  + {title} ({url})")


def main():
    # 1) 제목/태그라인
    try:
        wp("/settings", "POST", {"title": "제이로그", "description": "해외직구·통관·관세 가이드"})
        print("✅ 사이트 제목='제이로그', 태그라인='해외직구·통관·관세 가이드'")
    except Exception as e:
        print(f"::warning::제목/태그라인 설정 실패 — {e}")

    # 메뉴 위치 파악
    try:
        locs = wp("/menu-locations")
    except Exception as e:
        print(f"::warning::메뉴 위치 조회 실패({e}) — 이 테마는 REST 메뉴를 지원하지 않을 수 있음. "
              f"WP 관리자 > 외모 > 메뉴 에서 수동 정리가 필요합니다.")
        return
    loc_slugs = list(locs.keys()) if isinstance(locs, dict) else []
    print(f"등록된 메뉴 위치: {loc_slugs}")

    def pick(cands):
        for want in cands:
            for s in loc_slugs:
                if want in s.lower():
                    return s
        return None

    primary = pick(["primary", "main", "header", "top", "nav"]) or (loc_slugs[0] if loc_slugs else None)
    footer = pick(["footer", "bottom", "secondary", "social"])

    ids = {k: page_id(k) for k in ("blog", "about", "contact")}

    # 2) 메인 메뉴
    main_id = ensure_menu("제이로그 메인")
    print(f"메인 메뉴 id {main_id} 구성:")
    add_url_item(main_id, "홈", "https://jaylog.co.kr/", 1)
    add_page_item(main_id, "통관 진단", 464, 2)
    add_page_item(main_id, "관부가세 계산기", 253, 3)
    add_page_item(main_id, "블로그", ids["blog"], 4)
    add_page_item(main_id, "소개", ids["about"] or 86, 5)
    add_page_item(main_id, "문의", ids["contact"] or 192, 6)
    if primary:
        try:
            wp(f"/menus/{main_id}", "POST", {"locations": [primary]})
            print(f"✅ 메인 메뉴를 '{primary}' 위치에 배치")
        except Exception as e:
            print(f"::warning::메인 메뉴 위치 배치 실패 — {e}")
    else:
        print("::warning::기본 메뉴 위치를 찾지 못함 — 관리자에서 수동 배치 필요")

    # 3) 푸터 메뉴(법적 페이지)
    if footer:
        foot_id = ensure_menu("제이로그 푸터")
        print(f"푸터 메뉴 id {foot_id} 구성:")
        add_page_item(foot_id, "개인정보처리방침", 65, 1)
        add_page_item(foot_id, "DMCA", 67, 2)
        add_page_item(foot_id, "면책고지", 193, 3)
        add_page_item(foot_id, "문의", ids["contact"] or 192, 4)
        try:
            wp(f"/menus/{foot_id}", "POST", {"locations": [footer]})
            print(f"✅ 푸터 메뉴를 '{footer}' 위치에 배치")
        except Exception as e:
            print(f"::warning::푸터 메뉴 배치 실패 — {e}")
    else:
        print("ℹ️ 푸터 메뉴 위치가 없어 법적 페이지는 메인에서 제외만 함(푸터 위젯 등으로 노출 권장)")


if __name__ == "__main__":
    main()
