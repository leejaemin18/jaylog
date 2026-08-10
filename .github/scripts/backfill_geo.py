# 기존 발행글에 GEO 구조(한눈 요약 + FAQ + FAQPage JSON-LD)를 소급 적용한다.
# 데이터: geo/backfill.json = { "<post_id>": {"answer_summary": "...", "faq": [{"q","a"} x3]} }
# 라이브 글 본문을 가져와 render_geo로 주입 후 업데이트. 이미 주입된 글은 건너뛴다(멱등).
# 필요한 시크릿: WP_APP_PASSWORD  (OpenAI 불필요 — 텍스트 구조만 다룸)
import os, json, base64, urllib.request, urllib.error

from geo_render import render_geo

WP_USER = "claude"
WP_PW = os.environ["WP_APP_PASSWORD"]
API = "https://jaylog.co.kr/wp-json/wp/v2"
AUTH = base64.b64encode(f"{WP_USER}:{WP_PW}".encode()).decode()


def wp(path, method="GET", data=None):
    headers = {"Authorization": "Basic " + AUTH, "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(API + path, method=method, headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=120) as res:
        return json.load(res)


def main():
    data = json.load(open("geo/backfill.json", encoding="utf-8"))
    print(f"백필 데이터: {len(data)}개 글")
    done, skip, missing, failed = 0, 0, [], []
    for pid, meta in data.items():
        try:
            post = wp(f"/posts/{pid}?context=edit&_fields=id,content,title")
            body = post["content"]["raw"]
            if "geo-summary" in body and "FAQPage" in body:
                print(f"  [{pid}] 이미 적용됨 — 건너뜀")
                skip += 1
                continue
            new_body = render_geo(body, meta)
            if new_body == body:
                print(f"  [{pid}] 변경 없음 — 데이터 확인 필요")
                missing.append(pid)
                continue
            wp(f"/posts/{pid}", "POST", {"content": new_body})
            print(f"  [{pid}] ✅ {post['title']['raw'][:34]}")
            done += 1
        except urllib.error.HTTPError as e:
            detail = e.read()[:200].decode("utf-8", "replace")
            print(f"::warning::[{pid}] 실패 HTTP {e.code}: {detail}")
            failed.append(pid)
        except Exception as e:
            print(f"::warning::[{pid}] 실패: {e}")
            failed.append(pid)
    print(f"\n완료: 적용 {done} / 이미적용 {skip} / 데이터부족 {len(missing)} / 실패 {len(failed)}")
    if failed:
        print(f"실패 id: {failed}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
