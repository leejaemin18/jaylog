# 출처 및 라이선스 (NOTICE)

이 스킬(`humanize-korean`)은 아래 오픈소스를 제이로그 파이프라인용으로 이식·축약한 것입니다.

- **Humanize KR / im-not-ai** — https://github.com/epoko77-ai/im-not-ai (MIT License, © 2026 epoko77-ai)
  - 이식 대상: `references/`(taxonomy·quick-rules·playbook·metrics), `scripts/`(prepare_monolith_input·verify_change_rate).
  - 변경점: 짧은 블로그 글에 맞게 단일 콜 경로만 사용하는 SKILL.md로 재작성, 스크립트의 references 경로를 형제 폴더 기준으로 수정.
- **KatFishNet** — https://github.com/Shinwoo-Park/katfishnet (ACL 2025)
  - 위 도구의 판정 지표(띄어쓰기·POS 다양성·쉼표 사용 등 한국어 AI 텍스트 탐지 특징)의 학술적 근거.

원저작권 및 MIT 라이선스 전문은 각 원본 저장소를 따릅니다.
