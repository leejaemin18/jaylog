#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인스타 백로그 큐(research/insta-backlog-queue.md)에서 미발행 항목을 하루 최대 N개 인스타에 올린다.
- 각 항목: '## n) [완료?] post ...' 제목 + 'local_image:' + 'caption:' 블록(--- 로 구분).
- [완료] 없는 항목을 위에서부터 최대 MAX개 골라 insta_upload.py 로 게시(로컬 카드→WP 공개URL→IG).
- 캡션은 파일의 한글을 그대로 전달(유니코드 이스케이프 변환 없음 → 오타 원천 차단).
- 성공한 항목만 제목에 [완료] 표시. 파일이 바뀌면 워크플로가 커밋한다.
필요 시크릿: IG_USER_ID, IG_ACCESS_TOKEN, WP_APP_PASSWORD
"""
import os, re, subprocess, sys

QUEUE = "research/insta-backlog-queue.md"
MAX = int(os.environ.get("DAILY_MAX", "3"))


def parse_blocks(text):
    """--- 로 나눈 블록에서 (heading_line, local_image, caption, done) 추출."""
    blocks = []
    for chunk in text.split("\n---\n"):
        m = re.search(r"^(##\s*\d+\).*)$", chunk, re.M)
        if not m:
            continue
        heading = m.group(1)
        li = re.search(r"^local_image:\s*(.+)$", chunk, re.M)
        cap = re.search(r"^caption:\s*\n(.*)$", chunk, re.S | re.M)
        if not li or not cap:
            continue
        caption = cap.group(1).strip()
        blocks.append({
            "heading": heading,
            "local_image": li.group(1).strip(),
            "caption": caption,
            "done": "[완료]" in heading,
        })
    return blocks


def post_one(local_image, caption):
    cmd = [sys.executable, ".github/scripts/insta_upload.py",
           "--media-type", "IMAGE", "--local-image", local_image, "--caption", caption]
    r = subprocess.run(cmd)
    return r.returncode == 0


def main():
    text = open(QUEUE, encoding="utf-8").read()
    blocks = parse_blocks(text)
    pending = [b for b in blocks if not b["done"]]
    if not pending:
        print("백로그 소진 — 발행할 것 없음")
        return
    posted = 0
    for b in pending[:MAX]:
        print(f"▶ 게시: {b['heading']} ({b['local_image']})")
        if post_one(b["local_image"], b["caption"]):
            # 제목에 [완료] 삽입: '## n) ' 뒤에
            new_heading = re.sub(r"^(##\s*\d+\)\s*)", r"\1[완료] ", b["heading"])
            text = text.replace(b["heading"], new_heading, 1)
            posted += 1
            print(f"  ✅ 완료 표시: {new_heading}")
        else:
            print(f"  ⚠️ 게시 실패 — 완료 표시 안 함(다음 실행에 재시도): {b['heading']}")
            break  # 실패 시 중단(중복/과다 방지)
    open(QUEUE, "w", encoding="utf-8").write(text)
    remaining = len([b for b in parse_blocks(text) if not b["done"]])
    print(f"오늘 발행 {posted}개 / 남은 미발행 {remaining}개")


if __name__ == "__main__":
    main()
