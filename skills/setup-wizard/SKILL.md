---
name: setup-wizard
description: 사용자가 "/setup-wizard"를 실행하거나 "vault 초기 설정", "업종 설정", "온보딩 시작"이라고 말하면 이 스킬을 사용한다. 이 플러그인을 처음 설치한 직후, 그 업종에 맞는 vault(라우터, 규칙, 폴더 구조)를 생성할 때 쓴다.
---

# setup-wizard — 업종 전용 vault 온보딩

이 스킬은 claude-vault-framework 플러그인 설치 직후 1회 실행하는 것을 전제로 한다.
목표는 "raw/wiki 분리 + 다중 검증 + 확인 안 된 사실은 캐물어서 큐에 쌓는" 프레임워크를
사용자의 실제 업종에 맞게 즉석에서 조립하는 것이다.

**이 스킬 자신도 프레임워크의 uncertainty 원칙을 따른다** — 인터뷰에서 답이 안 나온 항목은
추측해서 채우지 않고 vault 생성 후 `tasks/questions/open-questions.md`에 큐로 남긴다.

## 인터뷰 순서 (한 번에 하나씩 질문)

1. **업종/도메인**: "어떤 업종·업무에서 쓸 vault인가요?" (자유 입력, 예: "동네 카페", "법무법인", "1인 프리랜서 디자이너")
2. **팀 규모**: 1인 / 소규모(2~10명) / 조직(10명+) — 이후 raw/wiki 접근 권한 안내 문구에 반영(이번 버전은 안내만, 실제 권한 제어는 하지 않음).
3. **고정 제약**: "이 업무에서 절대 바뀌지 않는 제약이 있나요? (예산, 규정, 인력 등)" — 자유 입력. 답이 "모르겠다"면 빈 문자열로 두고 open-questions.md에 큐로 남긴다.
4. **역할 분담 필요 여부**: "이 업무에 여러 역할(예: 주문 담당, 재고 담당)이 있고 그것마다 다른 규칙을 적용하고 싶나요?"
   - "아니오"면 5번으로 진행.
   - "예"면 역할 이름을 나열받아 라우터 "작업별 로드" 표에 들어갈 줄(`domain_rows`)과 "절대 규칙"에 들어갈 줄(`domain_absolute_rules`)을 함께 구성한다. 이 스킬은 역할 목록을 강제하지 않는다 — AURA의 backend-dev 같은 고정 에이전트 세트를 만들지 않고, 사용자가 부른 이름 그대로 표에 적는다.

## 실행

답변을 모은 뒤, vault root(현재 작업 디렉터리)를 대상으로 스크립트를 호출한다:

```bash
python <plugin-install-path>/skills/setup-wizard/generate.py
```

이 스크립트는 CLI 인자를 직접 받지 않는다 — 에이전트가 `generate_vault()` 함수를
아래 시그니처로 직접 호출하는 파이썬 한 줄을 실행하는 방식을 쓴다:

```bash
python -c "
import sys; sys.path.insert(0, r'<plugin-install-path>/skills/setup-wizard')
from generate import generate_vault
created = generate_vault(
    target_dir='.',
    domain='<1번 답변>',
    constraints='<3번 답변, 없으면 빈 문자열>',
    domain_rows='<4번에서 구성한 표 줄, 없으면 빈 문자열>',
    domain_absolute_rules='<4번에서 구성한 절대 규칙 줄, 없으면 빈 문자열>',
)
print(f'{len(created)}개 파일 생성 완료')
"
```

## 마무리

1. `constraints`가 빈 문자열이었으면, `tasks/questions/open-questions.md`에 "고정 제약 미확인" 항목을 하나 추가한다 (형식은 `.claude/rules/core/open-questions.md` 규칙 3번 참고).
2. 생성 직후 `python .claude/skills/verify-docs/check.py`를 1회 실행해 "OK: 6개 검사 통과"를 확인한다.
3. 사용자에게 안내: "vault가 생성됐습니다. 이제 실무 자료를 `AI-Sessions/raw/`에 넣고 `ingest`라고 말하면 가공을 시작합니다. 확인이 더 필요한 항목은 `tasks/questions/open-questions.md`에 쌓여 있으니 먼저 훑어보세요."
