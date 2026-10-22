# 발행된 글(published/<슬러그>.md)에 로컬 이미지(썸네일+본문)를 넣은 수정본을 만든다.
#   → revisions/post-<id>.html (본문) + revisions/post-<id>.json (제목·요약·대표이미지)
# 이후 blog-command의 apply-revisions가 이미지를 업로드하고 글에 반영한다(목차·편집자 박스도 그때 자동).
# 사용: python3 .github/scripts/make_revision.py published/<슬러그>.md <post id> ["alt1|alt2|alt3|alt4"]
import os, re, sys, json
import yaml

sys.path.insert(0, os.path.dirname(__file__))
from geo_render import render_geo

CALC_KEYS = {"일반", "의류", "가방", "건기식", "화장품", "전자0", "전자8"}
CALC_URL = "https://jaylog.co.kr/gwanbuga-calculator/"


def main():
    path, pid = sys.argv[1], int(sys.argv[2])
    alts = sys.argv[3].split("|") if len(sys.argv) > 3 else []
    text = open(path, encoding="utf-8").read()
    _, fm, body = text.split("---", 2)
    meta = yaml.safe_load(fm)
    body = re.sub(r"\n?<!-- 등록됨:.*?-->\s*$", "", body.strip(), flags=re.S)
    slug = meta["slug"]

    def has_img(name):
        return any(os.path.exists(f"drafts/img/{name}.{e}") for e in ("png", "jpg", "jpeg", "webp"))

    base_alt = meta.get("body_image_alt", meta["title"])
    n_img = 0
    for i, (suffix, marker) in enumerate([("body", "<!--본문이미지-->"), ("body2", "<!--본문이미지2-->"),
                                           ("body3", "<!--본문이미지3-->"), ("body4", "<!--본문이미지4-->")]):
        name = f"{slug}-{suffix}"
        if marker in body and has_img(name):
            alt = (alts[i] if i < len(alts) and alts[i].strip() else base_alt).replace('"', "'")
            fig = f'<figure class="wp-block-image size-large"><img src="LOCAL:{name}" alt="{alt}"/></figure>'
            body = body.replace(marker, fig, 1)
            n_img += 1

    calc = str(meta.get("calculator", "none")).strip()
    if calc in CALC_KEYS and CALC_URL not in body:
        btn = ('<p style="text-align:center;margin:1.6em 0;">'
               f'<a href="{CALC_URL}" style="display:inline-block;padding:12px 26px;'
               'background:#16233f;color:#e8c56f;border:1px solid #c9a44a;border-radius:8px;'
               'font-weight:700;text-decoration:none;">💰 관부가세 계산기로 내 예상 세금 계산하기 →</a></p>')
        body += "\n" + btn

    body = render_geo(body, meta)
    os.makedirs("revisions", exist_ok=True)
    open(f"revisions/post-{pid}.html", "w", encoding="utf-8").write(body + "\n")
    info = {"title": meta["title"], "excerpt": meta.get("excerpt", ""), "slug": slug}
    if has_img(f"{slug}-thumb"):
        info["featured_local"] = f"{slug}-thumb"
    json.dump(info, open(f"revisions/post-{pid}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    left = re.findall(r"<!--본문이미지\d?-->", body)
    print(f"post {pid}({slug}): 본문이미지 {n_img}개 삽입, 남은 마커 {len(left)}, "
          f"featured={'Y' if 'featured_local' in info else 'N'}")


if __name__ == "__main__":
    main()
