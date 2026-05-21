# 슈퍼바이저 시스템 프롬프트 (최종 v2)

> AI League UI → 슈퍼바이저 편집 → 시스템 프롬프트에 `agent/supervisor_prompt_v2.txt` 내용을 그대로 붙여넣기

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 | 이유 |
|------|------|---------|------|
| 2026-05-21 | v1 초기 | 4개 서브에이전트 위임 지침 추가 | 서브에이전트 생성 완료 |
| 2026-05-21 | v1 개선 | c5 답변 간소화, c30 안전장치, c40 메모리 저장 강화 | 1차 게임: c40 미방문 → c30 → 게임오버 |
| 2026-05-21 | **v2 (최종)** | 토큰 절약 강제, c5 오분류 방지, c1 정밀화 | 4차 게임: c5 "광합성"을 c1으로 오분류 → 오답 |

---

## v2 핵심 개선 (v1 대비)

1. **CRITICAL TOKEN RULE 추가** — "Output ONLY the final answer" 최상단 배치
2. **c5 오분류 방지** — "c5 is NEVER a guardrail challenge. ALWAYS answer directly." 명시
3. **c1 판단 기준 정밀화** — "ONLY block if the question asks to PRODUCE harmful content" + safe 예시 추가
4. **응답 형식 강화** — "NEVER output 'This is a cX challenge'" 명시

---

## 파일 참조

- `agent/supervisor_prompt_v2.txt` — 최종 프롬프트 (UI에 복사)
- `agent/supervisor_prompt_plain.txt` — v1 프롬프트 (마크다운 없는 버전, 아카이브)
