# revisions/post-{id}.html 의 새 본문을 워드프레스 해당 글에 적용한다 (blog-command: apply-revisions).
# revisions/post-{id}.json 이 있으면 excerpt 등 메타도 함께 갱신.
# 본문에 src="LOCAL:<파일명>" 이 있으면 drafts/img/<파일명>.(png|jpg…) 를 WP 미디어로 올리고
#   그 URL로 치환한다(본문 이미지 여러 장 삽입용, API 미호출·로컬 드라이브 이미지).
# 글 단위 실패 격리. 원문 백업은 review/post-{id}.md 에 이미 있음.
import os, re, json, base64, glob, io, urllib.request

from PIL import Image

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"


def wp(path, method="GET", data=None, raw=None, ctype="application/json", extra=None):
    headers = {"Authorization": "Basic " + AUTH, "Content-Type": ctype}
    if extra:
        headers.update(extra)
    body = raw if raw is not None else (json.dumps(data).encode() if data else None)
    req = urllib.request.Request(API + path, method=method, headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.load(res)


def upload_local_media(name):
    """drafts/img/<name>.(png|jpg…) 를 WP 미디어로 올리고 source_url을 돌려준다."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = f"drafts/img/{name}.{ext}"
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            b = io.BytesIO(); im.save(b, "JPEG", quality=88, optimize=True)
            media = wp("/media", "POST", raw=b.getvalue(), ctype="image/jpeg",
                       extra={"Content-Disposition": f'attachment; filename="{name}.jpg"'})
            print(f"    로컬 이미지 업로드: {name} → media {media['id']}")
            return media["source_url"]
    raise RuntimeError(f"LOCAL 이미지 파일 없음: drafts/img/{name}.*")


def resolve_local_images(body):
    """src="LOCAL:<name>" 을 실제 업로드 URL로 치환."""
    for name in sorted(set(re.findall(r'src="LOCAL:([^"]+)"', body))):
        url = upload_local_media(name)
        # 닫는 따옴표까지 포함해 정확히 치환 — 그러지 않으면 'body'가 'body2/3/4'의
        # 앞부분까지 바꿔(부분 문자열) URL이 깨진다(첫 장만 정상). (2026-09-11 수정)
        body = body.replace(f'LOCAL:{name}"', f'{url}"')
    return body


def main():
    files = sorted(glob.glob("revisions/post-*.html"),
                   key=lambda f: int(re.search(r"post-(\d+)", f).group(1)))
    if not files:
        print("적용할 수정본이 없습니다 (revisions/post-*.html)."); return
    done, failed = 0, []
    for f in files:
        pid = int(re.search(r"post-(\d+)", f).group(1))
        try:
            body = open(f, encoding="utf-8").read().strip()
            if len(body) < 300:
                raise RuntimeError(f"본문이 너무 짧음({len(body)}자) — 생성 오류 의심")
            body = resolve_local_images(body)  # LOCAL: 이미지 있으면 업로드·치환
            payload = {"content": body}
            metaf = f.replace(".html", ".json")
            if os.path.exists(metaf):
                meta = json.load(open(metaf, encoding="utf-8"))
                for k in ("excerpt", "title"):
                    if meta.get(k):
                        payload[k] = meta[k]
            r = wp(f"/posts/{pid}", "POST", payload)
            done += 1
            print(f"✅ 적용: id {pid} | {r['title']['rendered'][:36]}")
        except Exception as e:
            failed.append(pid)
            print(f"::warning::id {pid} 실패 — {e}")
    print(f"\n완료: 적용 {done} / 실패 {len(failed)}" + (f" {failed}" if failed else ""))


if __name__ == "__main__":
    main()
