# 로컬 이미지 파일(드라이브에서 받아 저장소에 커밋한 것)을 워드프레스 미디어로 올리고
# 지정한 글의 대표(썸네일) 이미지로 설정한다. OpenAI API를 쓰지 않는다(비용 0).
# 입력(환경변수): POST_ID = 대상 글 번호, IMAGE = 로컬 이미지 경로
# 필요한 시크릿: WP_APP_PASSWORD
import os, re, json, base64, io, urllib.request

from PIL import Image

WP_USER = "claude"
WP_PW = os.environ["WP_APP_PASSWORD"]
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


def upload(img):
    name = os.path.splitext(os.path.basename(img))[0]
    im = Image.open(img).convert("RGB")
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88, optimize=True)
    media = wp("/media", "POST", raw=b.getvalue(), ctype="image/jpeg",
               extra={"Content-Disposition": f'attachment; filename="{name}.jpg"'})
    print(f"업로드: media {media['id']} ({media['source_url']})")
    return media


def main():
    pid = os.environ["POST_ID"].strip()
    img = os.environ.get("IMAGE", "").strip()
    body_img = os.environ.get("BODY_IMAGE", "").strip()
    anchor = os.environ.get("BODY_ANCHOR", "").strip()  # 이 문구가 든 <h2> 앞에 본문이미지 삽입
    move_src = os.environ.get("MOVE_SRC", "").strip()   # 이미 삽입된 본문 figure를 올바른 위치로 이동(+alt 수정)
    new_title = os.environ.get("NEW_TITLE", "").strip()  # 글 제목 변경(포커스 키워드 앞배치 등)

    # 00) 제목 변경(있을 때만)
    if new_title:
        wp(f"/posts/{pid}", "POST", {"title": new_title})
        print(f"post {pid} 제목 변경 완료: {new_title}")

    # 0) 본문 이미지 재배치 모드 — 이미 삽입된 figure(파일명 일부=move_src)를 지워서 anchor h2 앞으로 옮기고 alt를 교정
    if move_src:
        post = wp(f"/posts/{pid}?context=edit&_fields=id,content")
        raw = post["content"]["raw"]
        pat = re.compile(r'<figure class="wp-block-image size-large"><img src="([^"]*'
                         + re.escape(move_src) + r'[^"]*)"[^>]*></figure>')
        m = pat.search(raw)
        if not m:
            raise SystemExit(f"이동할 figure 못 찾음: {move_src}")
        src_url = m.group(1)
        raw2 = raw[:m.start()] + raw[m.end():]
        fig = (f'<figure class="wp-block-image size-large"><img src="{src_url}" '
               f'alt="{os.environ.get("BODY_ALT", "")}" '
               f'style="border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,.08);"/></figure>')
        if not anchor:
            raise SystemExit("이동 모드에는 body_anchor가 필요합니다.")
        a = raw2.find(anchor)
        if a == -1:
            raise SystemExit(f"앵커 못 찾음(이동): {anchor}")
        idx = raw2.rfind("<h2", 0, a)
        if idx == -1:
            raise SystemExit(f"앵커 앞 h2 못 찾음(이동): {anchor}")
        new = raw2[:idx] + fig + raw2[idx:]
        wp(f"/posts/{pid}", "POST", {"content": new})
        print(f"post {pid} 본문 figure 재배치+alt 수정 완료 ({move_src} → '{anchor}' h2 앞)")
        return

    # 1) 대표(썸네일) 이미지 교체
    if img:
        if not os.path.exists(img):
            raise SystemExit(f"이미지 없음: {img}")
        media = upload(img)
        wp(f"/posts/{pid}", "POST", {"featured_media": media["id"]})
        print(f"post {pid} 대표 이미지 → media {media['id']} 로 교체 완료")

    # 2) 본문 이미지 삽입(있을 때만) — 이미 삽입돼 있으면 건너뜀
    if body_img:
        if not os.path.exists(body_img):
            raise SystemExit(f"본문 이미지 없음: {body_img}")
        media_b = upload(body_img)
        post = wp(f"/posts/{pid}?context=edit&_fields=id,content")
        raw = post["content"]["raw"]
        if media_b["source_url"] in raw:
            print("본문 이미지 이미 있음 — 건너뜀")
        else:
            fig = (f'<figure class="wp-block-image size-large"><img src="{media_b["source_url"]}" '
                   f'alt="{os.environ.get("BODY_ALT", "")}" '
                   f'style="border-radius:16px;box-shadow:0 4px 16px rgba(0,0,0,.08);"/></figure>')
            idx = -1
            if anchor:
                a = raw.find(anchor)
                if a != -1:
                    idx = raw.rfind("<h2", 0, a)
            if idx == -1:  # 앵커 실패 시 두 번째 h2 앞
                hs = [m.start() for m in re.finditer(r"<h2", raw)]
                idx = hs[1] if len(hs) >= 2 else (hs[0] if hs else len(raw))
            new = raw[:idx] + fig + raw[idx:]
            wp(f"/posts/{pid}", "POST", {"content": new})
            print(f"post {pid} 본문 이미지 삽입 완료 (media {media_b['id']})")


if __name__ == "__main__":
    main()
