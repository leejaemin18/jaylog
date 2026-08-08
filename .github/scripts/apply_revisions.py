# revisions/post-{id}.html 의 새 본문을 워드프레스 해당 글에 적용한다 (blog-command: apply-revisions).
# revisions/post-{id}.json 이 있으면 excerpt 등 메타도 함께 갱신.
# 글 단위 실패 격리. 원문 백업은 review/post-{id}.md 에 이미 있음.
import os, re, json, base64, glob, urllib.request

USER = "claude"
PW = os.environ["WP_APP_PASSWORD"]
AUTH = base64.b64encode(f"{USER}:{PW}".encode()).decode()
API = "https://jaylog.co.kr/wp-json/wp/v2"


def wp(path, method="GET", data=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": "Basic " + AUTH, "Content-Type": "application/json"},
        data=json.dumps(data).encode() if data else None)
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.load(res)


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
