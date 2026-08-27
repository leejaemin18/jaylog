#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
제이로그 인스타 업로더 — Instagram Graph API로 이미지/릴스 자동 게시.

인증(비밀): 환경변수로만 받는다. 절대 코드/로그에 토큰을 남기지 않는다.
  - IG_USER_ID       : 인스타 비즈니스/크리에이터 계정 ID
  - IG_ACCESS_TOKEN  : Meta 장기 액세스 토큰
선택(기본값 있음):
  - IG_GRAPH_HOST    : graph.instagram.com (기본) 또는 graph.facebook.com
  - IG_GRAPH_VERSION : v23.0 (기본)

사용:
  python insta_upload.py --image-url "https://.../card.jpg" --caption "본문..."
  python insta_upload.py --video-url "https://.../reel.mp4" --caption "..." --media-type REELS

미디어 URL은 반드시 외부에서 접근 가능한 '공개 URL'이어야 한다(워드프레스 미디어 등).
공식 2단계(컨테이너 생성 → 처리 대기 → 발행)를 따른다.
"""
import argparse
import base64
import glob
import io
import json
import os
import sys
import time
import urllib.request

import requests

HOST = os.environ.get("IG_GRAPH_HOST", "graph.instagram.com")
VERSION = os.environ.get("IG_GRAPH_VERSION", "v23.0")

# 워드프레스 미디어 업로드(공개 URL 확보용) — 인스타 Graph API는 공개 URL만 게시 가능.
WP_API = "https://jaylog.co.kr/wp-json/wp/v2"
WP_USER = "claude"


def wp_upload_local(name):
    """drafts/img/<name>.(jpg|png|…) 를 WP 미디어로 올리고 공개 source_url을 돌려준다."""
    pw = os.environ.get("WP_APP_PASSWORD")
    if not pw:
        sys.exit("❌ 로컬 이미지 게시에는 WP_APP_PASSWORD(시크릿)가 필요합니다.")
    matches = []
    for ext in ("jpg", "jpeg", "png", "webp"):
        matches += glob.glob(f"drafts/img/{name}.{ext}")
    if not matches:
        sys.exit(f"❌ 로컬 이미지 파일 없음: drafts/img/{name}.*")
    path = matches[0]
    auth = base64.b64encode(f"{WP_USER}:{pw}".encode()).decode()
    with open(path, "rb") as f:
        raw = f.read()
    ctype = "image/png" if path.endswith(".png") else "image/jpeg"
    fname = os.path.basename(path)
    req = urllib.request.Request(
        WP_API + "/media", method="POST", data=raw,
        headers={"Authorization": "Basic " + auth, "Content-Type": ctype,
                 "Content-Disposition": f'attachment; filename="{fname}"'})
    with urllib.request.urlopen(req, timeout=120) as res:
        media = json.load(res)
    print(f"  WP 미디어 업로드: {fname} → media {media['id']} / {media['source_url']}")
    return media["source_url"]


def _base():
    acc = os.environ["IG_USER_ID"]
    return f"https://{HOST}/{VERSION}/{acc}"


def _token():
    return os.environ["IG_ACCESS_TOKEN"]


def create_container(caption, image_url=None, video_url=None, media_type="IMAGE"):
    data = {"caption": caption, "access_token": _token()}
    if media_type == "REELS":
        data["media_type"] = "REELS"
        data["video_url"] = video_url
    else:
        data["image_url"] = image_url
    r = requests.post(f"{_base()}/media", data=data, timeout=60)
    j = r.json()
    if "id" not in j:
        sys.exit(f"❌ 컨테이너 생성 실패: {j.get('error', j)}")
    return j["id"]


def wait_ready(creation_id, tries=20, interval=6):
    """status_code가 FINISHED가 될 때까지 폴링(블라인드 sleep 대신 상태 확인)."""
    url = f"https://{HOST}/{VERSION}/{creation_id}"
    for i in range(tries):
        r = requests.get(url, params={"fields": "status_code", "access_token": _token()}, timeout=30)
        code = r.json().get("status_code")
        print(f"⏳ 처리 상태: {code} ({i+1}/{tries})")
        if code == "FINISHED":
            return True
        if code == "ERROR":
            sys.exit(f"❌ 미디어 처리 오류: {r.json()}")
        time.sleep(interval)
    print("⚠️ 처리 완료 확인 전에 발행 시도(계속)")
    return False


def publish(creation_id):
    r = requests.post(f"{_base()}/media_publish",
                      data={"creation_id": creation_id, "access_token": _token()}, timeout=60)
    j = r.json()
    if "id" not in j:
        sys.exit(f"❌ 발행 실패: {j.get('error', j)}")
    return j["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-url", default="")
    ap.add_argument("--video-url", default="")
    ap.add_argument("--local-image", default="",
                    help="drafts/img/<name>.* 를 WP 미디어에 올려 공개 URL로 게시(IMAGE)")
    ap.add_argument("--caption", default="")
    ap.add_argument("--media-type", default="IMAGE", choices=["IMAGE", "REELS"])
    a = ap.parse_args()

    for k in ("IG_USER_ID", "IG_ACCESS_TOKEN"):
        if not os.environ.get(k):
            sys.exit(f"❌ 환경변수 {k} 가 없습니다(시크릿 설정 필요).")

    # 로컬 카드가 지정되면 WP 미디어에 올려 공개 URL을 확보
    if a.local_image and not a.image_url:
        a.image_url = wp_upload_local(a.local_image)

    if a.media_type == "IMAGE" and not a.image_url:
        sys.exit("❌ IMAGE 게시에는 --image-url 또는 --local-image 가 필요합니다(공개 URL).")
    if a.media_type == "REELS" and not a.video_url:
        sys.exit("❌ REELS 게시에는 --video-url 이 필요합니다(공개 URL).")

    print(f"▶ 컨테이너 생성 ({a.media_type})…")
    cid = create_container(a.caption, a.image_url or None, a.video_url or None, a.media_type)
    print(f"  creation_id = {cid}")
    wait_ready(cid)
    mid = publish(cid)
    print(f"✅ 게시 완료 — media id: {mid}")


if __name__ == "__main__":
    main()
