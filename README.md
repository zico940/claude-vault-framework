# Claude Vault Framework

업종 무관 지식관리 프레임워크 — Claude Code 플러그인.

Raw/Wiki 분리, 확인되지 않은 사실은 큐에 쌓아 순서대로 캐묻는 인터뷰(uncertainty),
문서 간 정합성 다중 검증(verify-docs)을 뼈대로 삼는다.

## 설치

```
/plugin install claude-vault-framework
```

## 사용

설치 후 `/setup-wizard`를 실행하면 업종·팀 규모·역할을 인터뷰해
해당 업종 전용 vault(라우터, 규칙, 폴더 구조)를 생성한다.

## 구조

- `skills/setup-wizard/` — 온보딩 인터뷰 + vault 생성
- `skills/verify-docs/` — 문서 정합성 기계 검증
- `templates/` — wizard가 채워 넣는 원본 템플릿
