# 제이로그 워드프레스 연동 정보 (공개 가능 — 비밀키 제외)

> 🔑 비밀키(OpenAI API 키, 워드프레스 응용 프로그램 비밀번호)는 이 파일에 두지 않습니다.
> `secrets.local.md` 파일에 있으며 GitHub에는 올라가지 않습니다.

## 연동 개요
- 사이트: https://jaylog.co.kr
- 워드프레스 REST API 사용자: `claude` (관리자 권한)
- 인증: `secrets.local.md`의 응용 프로그램 비밀번호 사용
  - 예: `curl -u "claude:<비밀번호>" https://jaylog.co.kr/wp-json/wp/v2/posts`
- 썸네일 생성: OpenAI `gpt-image-2` 모델, 1536x1024 (키는 `secrets.local.md`)

## 사이트 구성 (2026-07-31 기준)
- 테마: GeneratePress (로워드 브릿지 세팅)
- 플러그인: AL Pack(프레스런) 1.3.1, Bridge Theme Assistant, Rank Math SEO
- 사이트 제목: "제이의 통관 무역(수입,수출,해외직구)에 대한 모든 이야기"
- **카테고리: 6 = 해외직구·통관 가이드 (단일 카테고리, 애드센스 주제 일관성용)**
  - 기본 카테고리도 6번으로 설정됨. Uncategorized(1)는 미사용.
- 글쓰기 에이전트: `agents/jaylog-writer.md` (원본 위치: `C:\CLAUDE\.claude\agents\jaylog-writer.md`)
- 글 계획/현황: `글계획.md`, `작성현황.md`

## 발행 정책
- **하루 1개씩만 발행** (애드센스 자연스럽게). 여러 개는 초안/예약발행으로 분산.
- 목표: 애드센스 승인 (전문성·일관성·생소함, 50대 타깃)
