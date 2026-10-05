# 사이트 구조 개편 (site-structure.yml) — '브랜드형 정보 사이트' 기준으로 jaylog를 정비한다.
# STEP 환경변수로 단계별 실행(각 단계 멱등, 다시 돌려도 안전):
#   profile    — 운영자 표시명 '제이' + 소개(bio) 갱신
#   categories — 카테고리 5개 생성/정리 + 발행글 재배정 (카테고리 6은 '통관 기초·조회'로 이름 변경해 재사용)
#   pages      — 신뢰 페이지 생성/갱신 (pages/*.html: 소개·운영자·편집원칙·문의·이용약관·면책·사이트맵)
#   home       — 대문 페이지를 assets/home.html로 갱신
#   furniture  — 전 발행글에 목차 + 하단 편집자 박스 삽입(jl_furniture, 원문은 review/backup-structure/에 백업)
#   nav        — 메인 메뉴(카테고리 중심) + 푸터 메뉴(신뢰 페이지) 재구성
# DRY_RUN=1 이면 쓰지 않고 계획만 출력. 결과는 review/site-structure.txt 에 누적 기록.
import os, re, sys, json, base64, html, datetime, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(__file__))
from jl_furniture import add_furniture

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"
SITE = "https://jaylog.co.kr"
DRY = os.environ.get("DRY_RUN", "") in ("1", "true", "yes")
LOG = []

OWNER = "제이"
BIO = ("해외직구·통관 정보 사이트 제이로그를 운영하는 제이입니다. 관세·면세 기준, 통관 절차, "
       "품목별 규정을 30~50대 직구족 눈높이에 맞춰 풀어 쓰고, 수치와 규정은 관세청·법령 등 "
       "공식 자료로 확인해 출처를 함께 적습니다.")

# (slug, 이름, 소개글, 글 id 목록). 첫 항목은 기존 카테고리 6을 이름만 바꿔 재사용한다.
CATEGORIES = [
    ("customs-basics", "통관 기초·조회",
     "직구 물건이 국내에 들어오는 과정과 그 과정을 직접 확인하는 방법을 다룹니다. "
     "개인통관고유부호 발급, 목록통관과 일반통관의 차이, 유니패스·배송조회로 통관 단계를 읽는 법, "
     "통관 용어와 배송 기간까지 직구를 처음 시작할 때 알아야 할 기본기를 모았습니다.",
     [23, 28, 40, 41, 325, 351, 398, 640, 655, 710, 1004, 1012]),
    ("duty-and-tax", "관세·면세 계산",
     "내 물건에 세금이 붙는지, 붙는다면 얼마인지 계산하는 방법을 정리합니다. "
     "150달러·미국 200달러 면세 기준, 관부가세 계산식, 합산과세, HS코드와 품목별 세율, "
     "선물·여행자 휴대품·이사물품 면세, 관세 납부와 과오납 환급까지 숫자와 근거 중심으로 설명합니다.",
     [19, 27, 32, 42, 53, 284, 317, 321, 532, 597, 610, 696, 1036]),
    ("country-and-shop", "나라·쇼핑몰별 직구",
     "어느 나라, 어느 쇼핑몰에서 사느냐에 따라 달라지는 배송·세금·주의점을 다룹니다. "
     "아마존(미국)·일본·중국(알리·테무·타오바오)·유럽 직구 첫걸음, 배송대행지와 직배송, 구매대행, "
     "해외원화결제(DCC), 블랙프라이데이 주문 시점까지 쇼핑 단계에서 알아둘 내용을 모았습니다.",
     [277, 330, 337, 340, 343, 415, 422, 449, 554, 969]),
    ("by-item", "품목별 직구",
     "물건 종류마다 다른 세율과 인증·수량 제한을 품목별로 정리합니다. "
     "전자제품 전파인증, 건강기능식품·영양제 수량, 의류·가방·명품 세율, 골프용품, 카메라·컴퓨터 부품, "
     "화장품, 유아용품, 주류처럼 자주 찾는 품목을 실제 계산 예시와 함께 다룹니다.",
     [43, 44, 55, 56, 58, 80, 390, 394, 409, 443, 458, 540, 567, 669, 946, 956, 980, 994,
      1044, 1053, 1061, 1069]),
    ("trouble-shooting", "통관 문제 해결",
     "직구 중 문제가 생겼을 때 무엇부터 해야 하는지 순서대로 안내합니다. "
     "통관 지연·보류·검사, 통관부호 오류, 관세 사칭 문자, 사기·미배송·파손·반품, "
     "짝퉁 적발과 되팔기, 저가신고 적발처럼 곤란한 상황의 원인과 대처법을 정리했습니다.",
     [92, 95, 98, 281, 333, 428, 581, 624, 939, 1020, 1028]),
]

# (slug, 제목, 파일) — 같은 slug 페이지가 있으면 본문만 갱신, 없으면 생성
PAGES = [
    ("about", "제이로그 소개", "pages/about.html"),
    ("editor", "운영자 소개 — 제이", "pages/editor.html"),
    ("editorial-policy", "편집 원칙", "pages/editorial-policy.html"),
    ("contact", "문의하기", "pages/contact.html"),
    ("terms", "이용약관", "pages/terms.html"),
    ("disclaimer", "면책고지", "pages/disclaimer.html"),
    ("sitemap", "사이트맵 — 전체 글 한눈에 보기", "pages/sitemap.html"),
]


def log(msg):
    print(msg)
    LOG.append(msg)


def wp(path, method="GET", data=None):
    if DRY and method != "GET":
        return {}
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data is not None else None)
    with urllib.request.urlopen(req, timeout=90) as res:
        return json.load(res)


def all_posts(fields="id,title,categories"):
    out, page = [], 1
    while True:
        try:
            batch = wp(f"/posts?status=publish&per_page=100&page={page}&_fields={fields}")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                break
            raise
        out += batch
        if len(batch) < 100:
            break
        page += 1
    return out


def cat_map():
    """slug → (id, link). 카테고리 단계를 먼저 돌린 뒤에만 5개가 모두 잡힌다."""
    cats = wp("/categories?per_page=100&_fields=id,slug,link,name,count")
    return {c["slug"]: (c["id"], c["link"]) for c in cats}


def fill(text, cmap):
    """{{CAT:slug}} → 카테고리 id, {{CATURL:slug}} → 카테고리 주소."""
    def rep(m):
        kind, slug = m.group(1), m.group(2)
        if slug not in cmap:
            raise RuntimeError(f"카테고리 '{slug}' 없음 — categories 단계를 먼저 실행하세요")
        return str(cmap[slug][0]) if kind == "CAT" else cmap[slug][1]
    return re.sub(r"\{\{(CAT|CATURL):([a-z-]+)\}\}", rep, text)


# ---------------- 단계별 ----------------

def step_profile():
    me = wp("/users/me?context=edit&_fields=id,name,slug,description")
    log(f"현재 저자: id={me['id']} name={me['name']} slug={me['slug']}")
    wp(f"/users/{me['id']}", "POST", {"name": OWNER, "nickname": OWNER, "description": BIO})
    log(f"✅ 표시명 '{OWNER}' + 소개 갱신")
    if me["slug"] != "jay":
        try:
            wp(f"/users/{me['id']}", "POST", {"slug": "jay"})
            log("✅ 저자 주소 slug → jay (/author/jay/)")
        except Exception as e:
            log(f"ℹ️ 저자 slug 변경 생략 — {e}")
    if not DRY:
        back = wp("/users/me?context=edit&_fields=name,slug,description")
        log(f"확인: name={back['name']} slug={back['slug']} bio={back['description'][:40]}…")


def step_categories():
    existing = wp("/categories?per_page=100&_fields=id,slug,name,count")
    by_slug = {c["slug"]: c for c in existing}
    log("기존 카테고리: " + ", ".join(f"{c['id']}:{c['name']}({c['count']})" for c in existing))
    ids = {}
    for i, (slug, name, desc, _) in enumerate(CATEGORIES):
        if slug in by_slug:
            cid = by_slug[slug]["id"]
            wp(f"/categories/{cid}", "POST", {"name": name, "description": desc})
            log(f"♻️ 카테고리 갱신: {cid} {name}")
        elif i == 0:
            cid = 6
            wp("/categories/6", "POST", {"name": name, "slug": slug, "description": desc})
            log(f"♻️ 카테고리 6 → '{name}' ({slug})로 이름 변경")
        else:
            r = wp("/categories", "POST", {"name": name, "slug": slug, "description": desc})
            cid = r.get("id", f"(신규:{slug})")
            log(f"✅ 카테고리 생성: {cid} {name}")
        ids[slug] = cid

    want = {}
    for slug, _, _, pids in CATEGORIES:
        for pid in pids:
            if pid in want:
                log(f"::warning::id {pid} 중복 배정 — {slug} 무시")
                continue
            want[pid] = ids[slug]
    posts = all_posts()
    moved = same = 0
    unmapped = []
    for p in posts:
        pid = p["id"]
        title = html.unescape(p["title"]["rendered"])[:40]
        if pid not in want:
            unmapped.append(f"{pid} {title}")
            continue
        target = [want[pid]]
        if p["categories"] == target:
            same += 1
            continue
        wp(f"/posts/{pid}", "POST", {"categories": target})
        moved += 1
        log(f"  → {pid} {title} : {p['categories']} → {target}")
    missing = sorted(set(want) - {p["id"] for p in posts})
    log(f"재배정 {moved} / 이미 맞음 {same} / 매핑 없음 {len(unmapped)} / 발행글 아님 {missing}")
    for u in unmapped:
        log(f"::warning::카테고리 매핑 없음(그대로 둠): {u}")


def step_pages():
    cmap = cat_map()
    for slug, title, path in PAGES:
        body = fill(open(path, encoding="utf-8").read().strip(), cmap)
        found = wp(f"/pages?slug={slug}&status=publish,draft,private&_fields=id")
        n = len(re.sub(r"\s", "", html.unescape(re.sub(r"<[^>]+>", "", body))))
        if found:
            pid = found[0]["id"]
            wp(f"/pages/{pid}", "POST", {"title": title, "content": body, "status": "publish"})
            log(f"♻️ 페이지 갱신: /{slug}/ (id {pid}, {n}자)")
        else:
            r = wp("/pages", "POST", {"title": title, "slug": slug, "content": body, "status": "publish"})
            log(f"✅ 페이지 생성: /{slug}/ (id {r.get('id')}, {n}자)")


def step_home():
    cmap = cat_map()
    body = fill(open("assets/home.html", encoding="utf-8").read(), cmap)
    found = wp("/pages?slug=home&status=publish,draft&_fields=id")
    if not found:
        raise RuntimeError("home 페이지 없음 — create-home-page를 먼저 실행")
    pid = found[0]["id"]
    wp(f"/pages/{pid}", "POST", {"content": body})
    log(f"♻️ 대문 페이지 갱신: id {pid}")


def step_furniture():
    posts = all_posts("id,title")
    os.makedirs("review/backup-structure", exist_ok=True)
    changed = same = failed = 0
    for p in posts:
        pid = p["id"]
        try:
            raw = wp(f"/posts/{pid}?context=edit&_fields=content")["content"]["raw"]
            new = add_furniture(raw)
            if new.strip() == raw.strip():
                same += 1
                continue
            bpath = f"review/backup-structure/post-{pid}.html"
            if not os.path.exists(bpath):  # 최초 원문만 보관
                with open(bpath, "w", encoding="utf-8") as f:
                    f.write(raw)
            wp(f"/posts/{pid}", "POST", {"content": new})
            toc = "목차O" if "<!--jl-toc-->" in new else "목차X(h2<3)"
            changed += 1
            log(f"  ✅ {pid} {html.unescape(p['title']['rendered'])[:34]} — {toc}")
        except Exception as e:
            failed += 1
            log(f"::warning::id {pid} 실패 — {e}")
    log(f"목차·편집자 박스: 변경 {changed} / 이미 동일 {same} / 실패 {failed}")


def page_id(slug):
    r = wp(f"/pages?slug={slug}&status=publish&_fields=id")
    return r[0]["id"] if r else None


def step_nav():
    try:
        locs = wp("/menu-locations")
    except Exception as e:
        log(f"::warning::메뉴 위치 조회 실패 — {e}")
        return
    loc_slugs = list(locs.keys()) if isinstance(locs, dict) else []
    log(f"메뉴 위치: {loc_slugs}")

    def pick(cands):
        for want in cands:
            for s in loc_slugs:
                if want in s.lower():
                    return s
        return None

    primary = pick(["primary", "main", "header", "top", "nav"]) or (loc_slugs[0] if loc_slugs else None)
    footer = pick(["footer", "bottom", "secondary"])

    def ensure_menu(name):
        for m in wp("/menus?per_page=100&_fields=id,name") or []:
            if m["name"] == name:
                for it in wp(f"/menu-items?menus={m['id']}&per_page=100&_fields=id") or []:
                    wp(f"/menu-items/{it['id']}?force=true", "DELETE")
                return m["id"]
        return wp("/menus", "POST", {"name": name}).get("id")

    def item(menu, order, title, **kw):
        data = {"title": title, "menus": menu, "status": "publish", "menu_order": order, **kw}
        wp("/menu-items", "POST", data)
        log(f"  + {title}")

    cmap = cat_map()
    main_id = ensure_menu("제이로그 메인")
    log(f"메인 메뉴 id {main_id}:")
    item(main_id, 1, "홈", type="custom", url=SITE + "/")
    for i, (slug, name, _, _) in enumerate(CATEGORIES, start=2):
        item(main_id, i, name, type="taxonomy", object="category", object_id=cmap[slug][0])
    item(main_id, 7, "관부가세 계산기", type="post_type", object="page", object_id=253)
    item(main_id, 8, "소개", type="post_type", object="page", object_id=page_id("about") or 86)
    if primary:
        wp(f"/menus/{main_id}", "POST", {"locations": [primary]})
        log(f"✅ 메인 메뉴 → '{primary}'")

    if footer:
        foot_id = ensure_menu("제이로그 푸터")
        log(f"푸터 메뉴 id {foot_id}:")
        order = 1
        for slug, title in (("editor", "운영자 소개"), ("editorial-policy", "편집 원칙"),
                            ("contact", "문의하기"), ("terms", "이용약관"),
                            ("disclaimer", "면책고지"), ("sitemap", "사이트맵")):
            pid = page_id(slug)
            if pid:
                item(foot_id, order, title, type="post_type", object="page", object_id=pid)
                order += 1
        item(foot_id, order, "개인정보처리방침", type="post_type", object="page", object_id=65)
        item(foot_id, order + 1, "DMCA", type="post_type", object="page", object_id=67)
        wp(f"/menus/{foot_id}", "POST", {"locations": [footer]})
        log(f"✅ 푸터 메뉴 → '{footer}'")
    else:
        log("ℹ️ 푸터 메뉴 위치 없음 — 푸터 링크는 대문·편집자 박스로 노출")


STEPS = {"profile": step_profile, "categories": step_categories, "pages": step_pages,
         "home": step_home, "furniture": step_furniture, "nav": step_nav}


def main():
    step = os.environ.get("STEP", "").strip()
    if step not in STEPS:
        sys.exit(f"STEP은 {list(STEPS)} 중 하나여야 함 (입력: {step!r})")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    log(f"=== {now:%Y-%m-%d %H:%M} KST · STEP={step}{' (DRY_RUN)' if DRY else ''} ===")
    try:
        STEPS[step]()
    finally:
        os.makedirs("review", exist_ok=True)
        with open("review/site-structure.txt", "a", encoding="utf-8") as f:
            f.write("\n".join(LOG) + "\n\n")


if __name__ == "__main__":
    main()
