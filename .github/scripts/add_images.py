# 텍스트로만 등록된 글(크레딧 소진 때 '썸네일 필요')에 나중에 이미지를 채운다.
# 입력: 환경변수 FILE = published/<슬러그>.md (thumbnail_brief/body_image_brief + '등록됨: post NNN' 주석 필요)
# 동작: 썸네일 생성→업로드→featured_media 지정. body_image_brief 있으면 본문 이미지도 생성·삽입.
# 필요한 시크릿: WP_APP_PASSWORD, OPENAI_API_KEY
import os, re, json, base64, io, urllib.request, urllib.error

import yaml
from PIL import Image

WP_USER = "claude"
WP_PW = os.environ["WP_APP_PASSWORD"]
OPENAI_KEY = os.environ["OPENAI_API_KEY"]
API = "https://jaylog.co.kr/wp-json/wp/v2"
AUTH = base64.b64encode(f"{WP_USER}:{WP_PW}".encode()).decode()


def wp(path, method="GET", data=None, raw=None, ctype="application/json", extra=None):
    headers = {"Authorization": "Basic " + AUTH, "Content-Type": ctype}
    if extra:
        headers.update(extra)
    body = raw if raw is not None else (json.dumps(data).encode() if data else None)
    req = urllib.request.Request(API + path, method=method, headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=300) as res:
        return json.load(res)


def openai_image(prompt):
    payload = {"model": "gpt-image-2", "prompt": prompt, "size": "1536x1024", "quality": "high"}
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", method="POST",
        headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
        data=json.dumps(payload).encode())
    with urllib.request.urlopen(req, timeout=300) as res:
        out = json.load(res)
    return base64.b64decode(out["data"][0]["b64_json"])


def upload(brief, slug, suffix):
    png = openai_image(brief)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88, optimize=True)
    return wp("/media", "POST", raw=b.getvalue(), ctype="image/jpeg",
              extra={"Content-Disposition": f'attachment; filename="{slug}-{suffix}.jpg"'})


def main():
    path = os.environ["FILE"]
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta = yaml.safe_load(m.group(1))
    pid_m = re.search(r"등록됨: post (\d+)", text)
    if not pid_m:
        raise SystemExit(f"{path}: '등록됨: post NNN' 주석을 찾을 수 없음")
    pid = pid_m.group(1)
    slug = re.sub(r"[^a-z0-9]+", "-", meta.get("slug", "post").lower()).strip("-") or "post"
    print(f"대상: post {pid} ({meta.get('title','')[:30]})")

    # 1) 썸네일 → featured_media
    media = upload(meta["thumbnail_brief"], slug, "thumb")
    wp(f"/posts/{pid}", "POST", {"featured_media": media["id"]})
    print(f"  썸네일 media {media['id']} → featured_media 지정")

    # 2) 본문 이미지 (아직 없으면 삽입)
    if meta.get("body_image_brief"):
        post = wp(f"/posts/{pid}?context=edit&_fields=content")
        body = post["content"]["raw"]
        if f"{slug}-body" in body:
            print("  본문 이미지 이미 있음 — 건너뜀")
        else:
            media2 = upload(meta["body_image_brief"], slug, "body")
            alt = meta.get("body_image_alt", meta.get("title", ""))
            fig = (f'<figure class="wp-block-image size-large">'
                   f'<img src="{media2["source_url"]}" alt="{alt}"/></figure>')
            if "<!--본문이미지-->" in body:
                body = body.replace("<!--본문이미지-->", fig, 1)
            else:
                parts = re.split(r"(?=<h2)", body)
                body = (parts[0] + parts[1] + fig + "".join(parts[2:])) if len(parts) >= 3 else body + fig
            wp(f"/posts/{pid}", "POST", {"content": body})
            print(f"  본문 이미지 media {media2['id']} 삽입")
    print("완료")


if __name__ == "__main__":
    main()
