# 로컬 이미지 파일(드라이브에서 받아 저장소에 커밋한 것)을 워드프레스 미디어로 올리고
# 지정한 글의 대표(썸네일) 이미지로 설정한다. OpenAI API를 쓰지 않는다(비용 0).
# 입력(환경변수): POST_ID = 대상 글 번호, IMAGE = 로컬 이미지 경로
# 필요한 시크릿: WP_APP_PASSWORD
import os, json, base64, io, urllib.request

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


def main():
    pid = os.environ["POST_ID"].strip()
    img = os.environ["IMAGE"].strip()
    if not os.path.exists(img):
        raise SystemExit(f"이미지 없음: {img}")
    name = os.path.splitext(os.path.basename(img))[0]

    im = Image.open(img).convert("RGB")
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88, optimize=True)
    media = wp("/media", "POST", raw=b.getvalue(), ctype="image/jpeg",
               extra={"Content-Disposition": f'attachment; filename="{name}.jpg"'})
    print(f"업로드: media {media['id']} ({media['source_url']})")

    wp(f"/posts/{pid}", "POST", {"featured_media": media["id"]})
    print(f"post {pid} 대표 이미지 → media {media['id']} 로 교체 완료")


if __name__ == "__main__":
    main()
