# Claude Vault Framework

업종 무관 지식관리 프레임워크 — Claude Code 스킬.

Raw/Wiki 분리, 확인되지 않은 사실은 큐에 쌓아 순서대로 캐묻는 인터뷰(uncertainty),
문서 간 정합성 다중 검증(verify-docs)을 뼈대로 삼는다.

## 설치

이 저장소를 클론한 뒤 `setup-wizard/` 폴더를 스킬 디렉터리로 복사한다.

**모든 프로젝트에서 쓰고 싶으면** (사용자 전역):
```bash
git clone https://github.com/zico940/claude-vault-framework.git
cp -r claude-vault-framework/setup-wizard ~/.claude/skills/setup-wizard
```

**특정 프로젝트에서만 쓰고 싶으면** (프로젝트 로컬):
```bash
git clone https://github.com/zico940/claude-vault-framework.git
cp -r claude-vault-framework/setup-wizard <프로젝트 경로>/.claude/skills/setup-wizard
```

별도 설치 명령이나 marketplace 등록 절차가 없다 — 폴더를 이 위치에 두면
Claude Code가 자동으로 스킬을 인식한다.

## 사용

설치 후 대화에서 "vault 초기 설정해줘" 또는 `/setup-wizard`라고 말하면
업종·팀 규모·역할을 인터뷰해 해당 업종 전용 vault(라우터, 규칙, 폴더 구조)를 생성한다.

## 구조

```
setup-wizard/
  SKILL.md              — 온보딩 인터뷰 흐름 안내
  generate.py            — 인터뷰 답변으로 vault를 생성하는 로직
  verify_docs.py          — 문서 정합성 검증기 (생성된 vault에 check.py로 배치됨)
  verify_docs_SKILL.md     — 검증기 사용 안내 (생성된 vault에 SKILL.md로 배치됨)
  templates/               — CLAUDE.md·라우터·핵심 규칙 4종 원본 템플릿
```
