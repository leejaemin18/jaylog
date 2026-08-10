---
name: humanize-korean
description: AI(ChatGPT·Claude·Gemini 등)가 쓴 한글 글의 "AI 티"를 내용은 한 글자도 안 건드리고 문체·리듬·표현만 자연스러운 한국어로 되돌린다. 번역투("~를 통해/~에 있어서"), 상투구("결론적으로/시사하는 바가 크다"), 기계적 병렬("첫째·둘째·셋째"), 피동·문두 접속사·이모지/불릿 남발 등 10대 카테고리 70패턴을 심각도(S1/S2/S3)로 탐지·윤문. 트리거 — "AI 티 없애줘", "GPT 문체 제거", "사람이 쓴 것처럼 윤문", "번역투 제거", "한글 AI 윤문", "humanize". 제이로그 초안(짧은 블로그 글)은 단일 콜로 처리한다.
---

# humanize-korean (제이로그 이식판) — AI 한글 티 제거

> 출처: [epoko77-ai/im-not-ai](https://github.com/epoko77-ai/im-not-ai) (Humanize KR, MIT).
> 판정 지표의 학술 근거: [Shinwoo-Park/katfishnet](https://github.com/Shinwoo-Park/katfishnet) (KatFishNet, ACL 2025).
> 제이로그는 짧은 정보성 블로그 글이라 원본의 3-에이전트 오케스트레이터 대신 **단일 콜 경로**만 쓴다.
> 원본 전체 규칙: `references/` (taxonomy·playbook·quick-rules).

## 4대 철칙 (절대 위반 금지)
1. **의미 불변** — 사실·주장·수치·고유명사·직접 인용은 100% 보존. **관세율·면세기준·날짜 등 숫자는 절대 바꾸지 말 것**(우리 도메인 최우선).
2. **근거 기반** — 탐지된 부분(span)만 수술적 수정. 탐지 없는 구간은 손대지 않는다.
3. **장르 유지** — 정보성 블로그의 결을 유지(문학·에세이로 바꾸지 않음).
4. **과윤문 금지** — 변경률 30% 초과 경고, 50% 초과 중단(아래 게이트로 검증).

## 절차 (단일 콜)

### 1. 점수 확인 (선택, 권장)
```
python3 .claude/skills/humanize-korean/scripts/prepare_monolith_input.py --text "<원문>" --genre blog
```
→ `route_hint`(light/standard/heavy)·`risk`·간섭지수를 참고. (블로그 초안은 대개 light~standard.)

### 2. 탐지 + 윤문 (한 번에)
`references/quick-rules.md`(핵심 규칙)와 `references/ai-tell-taxonomy.md`(전체 70패턴)를 기준으로,
아래 우선순위로 **탐지된 것만** 고친다:
- **S1(무조건 제거)**: "결론적으로/종합하면", "시사하는 바가 크다", "주목할 만하다", "~라 할 수 있다", 이중피동("되어진다"), 기계적 "첫째·둘째·셋째".
- **S2(반복 시 제거)**: 번역투 "~를 통해/~에 있어서/가지고 있다/~에 대해", 문두 접속사 연발("또한/따라서/그리고"), hedging "~할 수 있을 것으로 보인다".
- **S3(중첩 시)**: 과도한 **볼드**·이모지·불릿, "매우/정말" 수식, 형식명사("것이다/점/수/바") 과다.
- 윤문 방향은 `references/rewriting-playbook.md`의 before→after 예시를 따른다.
- 문장 길이·종결어미를 일부러 들쭉날쭉하게(사람 글은 리듬이 불균일하다).

### 3. 변경률 게이트 (필수)
윤문 전/후를 파일로 저장하고:
```
python3 .claude/skills/humanize-korean/scripts/verify_change_rate.py --before before.txt --after after.txt --ignore-markup
```
- exit 0=수렴(채택) / 1=경고(사용자 고지) / 2=중단(30~50%↑ 과윤문 → 롤백·재시도).

## 제이로그 파이프라인 연동
- **발행 전 자동 게이트**: `publish-draft.yml`이 초안 등록 전 `humanize_gate.py`로 AI 티를 점수화해
  경고를 남긴다(비차단). 경고가 뜬 초안은 이 스킬로 윤문 후 다시 커밋한다.
- **글 쓸 때**: 초안을 drafts/에 커밋하기 **전에** 이 스킬로 한 번 훑는다(agents/jaylog-writer.md 규칙).
- **기존 글 점검**: 폰 명령 `humanize-audit` → 라이브 글의 AI 티 현황을 review/humanize-audit.txt로.
