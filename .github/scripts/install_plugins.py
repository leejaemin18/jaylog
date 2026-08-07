# 워드프레스에 플러그인을 원격 설치·활성화하는 스크립트 (blog-command의 install-plugins 명령).
# WP REST API의 /wp/v2/plugins 엔드포인트 사용 (관리자 권한 필요).
import os, json, base64, urllib.request, urllib.error

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"

# 설치할 플러그인 (wordpress.org 슬러그)
PLUGINS = [
    ("google-site-kit", "Site Kit by Google — 서치콘솔·애널리틱스·애드센스 연결"),
    ("webp-converter-for-media", "Converter for Media — 이미지 WebP 자동 변환(속도)"),
    ("easy-table-of-contents", "Easy Table of Contents — 글 목차 자동 생성(체류시간)"),
    ("insert-headers-and-footers", "WPCode — 애드센스 검증코드 등 삽입용"),
]


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=180) as res:
        return json.load(res)


def main():
    try:
        installed = wp("/plugins?per_page=100&_fields=plugin,status,name")
    except urllib.error.HTTPError as e:
        print(f"::error::플러그인 목록 조회 실패 HTTP {e.code} — claude 계정이 관리자인지 확인 필요: {e.read()[:300].decode('utf-8','replace')}")
        raise SystemExit(1)
    have = {p["plugin"].split("/")[0]: p["status"] for p in installed}
    print("현재 설치된 플러그인:", ", ".join(f"{k}({v})" for k, v in have.items()))
    for slug, desc in PLUGINS:
        if slug in have:
            if have[slug] != "active":
                target = next(p["plugin"] for p in installed if p["plugin"].split("/")[0] == slug)
                wp(f"/plugins/{target.replace('/', '%2F')}", "POST", {"status": "active"})
                print(f"🔛 활성화: {slug}")
            else:
                print(f"이미 활성: {slug}")
            continue
        try:
            r = wp("/plugins", "POST", {"slug": slug, "status": "active"})
            print(f"✅ 설치+활성화: {slug} — {desc} (버전 {r.get('version','?')})")
        except urllib.error.HTTPError as e:
            print(f"::warning::{slug} 설치 실패 HTTP {e.code}: {e.read()[:300].decode('utf-8','replace')}")


if __name__ == "__main__":
    main()
