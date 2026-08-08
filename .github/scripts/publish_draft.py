# drafts/ 폴더의 초안을 워드프레스에 등록하는 클라우드 스크립트.
# 초안 형식은 CLAUDE.md의 "drafts/ 초안 형식" 참고.
import os, re, json, base64, glob, shutil, datetime, urllib.request, io

import yaml
from PIL import Image

WP_USER = "claude"
WP_PW = os.environ["WP_APP_PASSWORD"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
API = "https://jaylog.co.kr/wp-json/wp/v2"
AUTH = base64.b64encode(f"{WP_USER}:{WP_PW}".encode()).decode()
KST = datetime.timezone(datetime.timedelta(hours=9))
PUBLISH_TIMES = ["08:40", "12:25", "20:35", "17:10", "09:55", "21:20", "14:05"]


def wp(path, method="GET", data=None, raw=None, ctype="application/json", extra=None):
    headers = {"Authorization": "Basic " + AUTH, "Content-Type": ctype}
    if extra:
        headers.update(extra)
    body = raw if raw is not None else (json.dumps(data).encode() if data else None)
    req = urllib.request.Request(API + path, method=method, headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.load(res)


def openai_image(prompt):
    payload = {"model": "gpt-image-2", "prompt": prompt, "size": "1536x1024", "quality": "high"}
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", method="POST",
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
        data=json.dumps(payload).encode())
    try:
        with urllib.request.urlopen(req, timeout=300) as res:
            out = json.load(res)
    except urllib.error.HTTPError as e:
        body = e.read()[:500].decode("utf-8", "replace")
        raise RuntimeError(f"OpenAI 이미지 생성 실패 HTTP {e.code}: {body}") from None
    return base64.b64decode(out["data"][0]["b64_json"])


def make_tag_ids(names):
    ids = []
    for name in names:
        try:
            ids.append(wp("/tags", "POST", {"name": name})["id"])
        except urllib.error.HTTPError as e:
            info = json.load(e)
            if info.get("code") == "term_exists":
                ids.append(info["data"]["term_id"])
            else:
                raise
    return ids


def next_slot():
    """내일부터 예약이 없는 첫 날을 찾아 배정 (하루 1개, 빈 날짜 우선 채움)."""
    future = wp("/posts?status=future&per_page=100&_fields=date")
    taken = {datetime.datetime.fromisoformat(p["date"]).date() for p in future}
    d = datetime.datetime.now(KST).date() + datetime.timedelta(days=1)
    while d in taken:
        d += datetime.timedelta(days=1)
    hh, mm = PUBLISH_TIMES[d.toordinal() % len(PUBLISH_TIMES)].split(":")
    return f"{d.isoformat()}T{hh}:{mm}:00"


def process(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        print(f"::warning::{path}: frontmatter(---) 형식이 아님 — 건너뜀")
        return False
    meta, body = yaml.safe_load(m.group(1)), m.group(2).strip()
    title = meta["title"]
    print(f"처리 중: {title}")

    # 1) 썸네일 생성 + 업로드
    png = openai_image(meta["thumbnail_brief"])
    img = Image.open(io.BytesIO(png)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True)
    slug = re.sub(r"[^a-z0-9]+", "-", meta.get("slug", os.path.basename(path)[:-3]).lower()).strip("-") or "post"
    media = wp("/media", "POST", raw=buf.getvalue(), ctype="image/jpeg",
               extra={"Content-Disposition": f'attachment; filename="{slug}-thumb.jpg"'})
    print(f"  썸네일 업로드: media {media['id']}")

    # 1-b) 본문 이미지 생성 + 업로드 + 삽입 (body_image_brief가 있으면)
    if meta.get("body_image_brief"):
        png2 = openai_image(meta["body_image_brief"])
        img2 = Image.open(io.BytesIO(png2)).convert("RGB")
        buf2 = io.BytesIO()
        img2.save(buf2, "JPEG", quality=88, optimize=True)
        media2 = wp("/media", "POST", raw=buf2.getvalue(), ctype="image/jpeg",
                    extra={"Content-Disposition": f'attachment; filename="{slug}-body.jpg"'})
        print(f"  본문 이미지 업로드: media {media2['id']}")
        alt = meta.get("body_image_alt", title)
        fig = (f'<figure class="wp-block-image size-large">'
               f'<img src="{media2["source_url"]}" alt="{alt}"/></figure>')
        if "<!--본문이미지-->" in body:
            body = body.replace("<!--본문이미지-->", fig, 1)
        else:  # 마커가 없으면 두 번째 h2 앞(첫 섹션 끝)에 삽입
            parts = re.split(r"(?=<h2)", body)
            if len(parts) >= 3:
                body = parts[0] + parts[1] + fig + "".join(parts[2:])
            else:
                body += fig

    # 1-c) 관부가세 계산기 — 세금 계산과 관련된 글이면 계산기 전용 페이지로 가는 버튼 링크를 넣는다.
    # (예전엔 계산기 위젯 HTML을 글마다 인라인 복붙했으나, 애드센스가 '복붙 중복'으로 감점 →
    #  독립 페이지 1개로 분리하고 링크만 넣는 방식으로 변경. calculator 필드는 '세금 관련 글인가' 표시로만 사용.)
    CALC_KEYS = {"일반", "의류", "가방", "건기식", "화장품", "전자0", "전자8"}
    calc_key = str(meta.get("calculator", "none")).strip()
    CALC_URL = "https://jaylog.co.kr/gwanbuga-calculator/"
    if calc_key in CALC_KEYS and CALC_URL not in body:
        btn = ('<p style="text-align:center;margin:1.6em 0;">'
               f'<a href="{CALC_URL}" style="display:inline-block;padding:12px 26px;'
               'background:#16233f;color:#e8c56f;border:1px solid #c9a44a;border-radius:8px;'
               'font-weight:700;text-decoration:none;">💰 관부가세 계산기로 내 예상 세금 계산하기 →</a></p>')
        notice = "<p><em>본 글은 일반 정보"
        if notice in body:
            body = body.replace(notice, btn + "\n" + notice, 1)
        else:
            body += "\n" + btn

    # 2) 글 등록 (예약 큐 맨 뒤)
    mode = meta.get("schedule", "auto")
    post = {
        "title": title, "content": body, "categories": [int(meta.get("category", 6))],
        "featured_media": media["id"], "tags": make_tag_ids(meta.get("tags", [])),
        "excerpt": meta.get("excerpt", ""),
    }
    if mode == "now":
        post["status"] = "publish"
    elif mode == "draft":
        post["status"] = "draft"
    else:  # auto → 하루 1개 예약 큐
        post["status"] = "future"
        post["date"] = next_slot()
    created = wp("/posts", "POST", post)
    when = created.get("date", "")
    print(f"  등록 완료: post {created['id']} | {created['status']} | {when}")

    # 3) 초안 파일을 published/로 이동 + 기록
    os.makedirs("published", exist_ok=True)
    dest = os.path.join("published", os.path.basename(path))
    shutil.move(path, dest)
    with open(dest, "a", encoding="utf-8") as f:
        f.write(f"\n\n<!-- 등록됨: post {created['id']} / {created['status']} / {when} / media {media['id']} -->\n")
    with open("작성현황.md", "a", encoding="utf-8") as f:
        f.write(f"\n- [클라우드 자동] {title} → post {created['id']} ({created['status']} {when})")
    return True


def main():
    drafts = sorted(glob.glob("drafts/*.md"))
    drafts = [d for d in drafts if not d.endswith(".gitkeep")]
    if not drafts:
        print("처리할 초안 없음")
        return
    done, failed = 0, []
    for d in drafts:
        try:
            if process(d):
                done += 1
        except Exception as e:  # 한 글이 실패해도 나머지는 계속 처리
            failed.append(d)
            print(f"::error::{d} 처리 실패 — {e}")
    print(f"완료: {done}/{len(drafts)}개 등록" + (f", 실패 {len(failed)}건: {failed}" if failed else ""))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
