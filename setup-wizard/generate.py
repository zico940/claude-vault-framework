#!/usr/bin/env python3
"""setup-wizard 인터뷰 답변을 받아 업종 전용 vault를 생성한다.

이 스크립트는 파일 생성만 담당한다. 인터뷰(질문 순서, 문구)는
SKILL.md가 대화형으로 진행하고, 답변을 모은 뒤 이 스크립트를 호출한다.
"""
import os
import shutil

SKILL_ROOT = os.path.dirname(os.path.abspath(__file__))

CORE_RULE_FILES = ("file-ops.md", "uncertainty.md", "open-questions.md", "rule-authoring.md")


def _write(target_dir, rel_path, content):
    full = os.path.join(target_dir, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def _read_template(rel_path):
    with open(os.path.join(SKILL_ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


def generate_vault(
    target_dir, domain, constraints, domain_rows="", domain_absolute_rules="", platform="claude"
):
    """업종 전용 vault를 target_dir에 생성한다.

    Args:
        target_dir: vault를 생성할 디렉터리(이미 존재해야 함).
        domain: 업종/도메인 이름 (예: "동네 카페").
        constraints: 이 업무의 고정 제약 (예: "1인 운영, 외부 고객 데이터 없음").
            open-questions.md의 권장안 근거 문구에 들어간다.
        domain_rows: 라우터 "작업별 로드" 표에 추가할 줄(없으면 빈 문자열).
        domain_absolute_rules: 라우터 "절대 규칙"에 추가할 줄(없으면 빈 문자열).
        platform: "claude" | "codex" | "both". verify-docs 트리거를 어느 CLI 관례로
            배치할지 결정한다. check.py 로직 자체는 플랫폼 무관, 트리거 안내문의
            배치 위치/형식만 달라진다.

    Returns:
        생성된 파일의 target_dir 기준 상대경로 목록.
    """
    if platform not in ("claude", "codex", "both"):
        raise ValueError(f"알 수 없는 platform: {platform!r} (claude/codex/both 중 하나)")
    created = []

    # 1. CLAUDE.md (vault 지식관리 규칙)
    claude_md = _read_template("templates/CLAUDE.md.template").replace("{{domain}}", domain)
    _write(target_dir, "CLAUDE.md", claude_md)
    created.append("CLAUDE.md")

    # 2. .claude/CLAUDE.md (라우터)
    router = (
        _read_template("templates/router.md.template")
        .replace("{{domain_rows}}", domain_rows)
        .replace("{{domain_absolute_rules}}", domain_absolute_rules)
    )
    _write(target_dir, ".claude/CLAUDE.md", router)
    created.append(".claude/CLAUDE.md")

    # 3. .claude/rules/core/*.md
    for name in CORE_RULE_FILES:
        content = _read_template(f"templates/rules/core/{name}")
        if name == "open-questions.md":
            content = content.replace("{{도메인_제약}}", constraints)
        _write(target_dir, f".claude/rules/core/{name}", content)
        created.append(f".claude/rules/core/{name}")

    # 4. verify-docs 검증기 이식. check.py 로직은 플랫폼 무관이라 항상 같은 위치에
    # 둔다 — .claude/CLAUDE.md든 AGENTS.md든 check.py가 스스로 찾아서 검사한다.
    # 트리거(언제 실행할지 안내)만 플랫폼별 관례에 맞춰 다르게 배치한다.
    verify_docs_dst = os.path.join(target_dir, ".claude", "skills", "verify-docs")
    os.makedirs(verify_docs_dst, exist_ok=True)
    shutil.copy(os.path.join(SKILL_ROOT, "verify_docs.py"), os.path.join(verify_docs_dst, "check.py"))
    created.append(".claude/skills/verify-docs/check.py")

    if platform in ("claude", "both"):
        shutil.copy(os.path.join(SKILL_ROOT, "verify_docs_SKILL.md"), os.path.join(verify_docs_dst, "SKILL.md"))
        created.append(".claude/skills/verify-docs/SKILL.md")

    if platform in ("codex", "both"):
        agents_section = _read_template("verify_docs_AGENTS.md.template")
        agents_path = os.path.join(target_dir, "AGENTS.md")
        if os.path.exists(agents_path):
            with open(agents_path, "a", encoding="utf-8") as f:
                f.write("\n" + agents_section)
        else:
            _write(target_dir, "AGENTS.md", agents_section)
        created.append("AGENTS.md")

    # 5. tasks/questions/open-questions.md (빈 큐)
    queue = (
        "# open-questions — 확인 필요 사항 큐\n\n"
        "절차: [[.claude/rules/core/open-questions.md]]\n\n"
        "## 0. 먼저 답해주세요(선행)\n\n"
        "(현재 없음)\n\n"
        "## A. 인프라·운영\n\n"
        "## B. 업무 프로세스\n\n"
        "## C. 범위·데이터\n\n"
    )
    _write(target_dir, "tasks/questions/open-questions.md", queue)
    created.append("tasks/questions/open-questions.md")

    # 6. log.md, index.md (빈 시작 파일)
    _write(target_dir, "log.md", "# log\n\n작업 로그. 형식: `YYYY-MM-DD HH:mm | command | 내용 | 링크`\n")
    created.append("log.md")
    _write(target_dir, "index.md", f"# {domain} 업무 vault\n\n## 최근 문서\n\n(아직 없음)\n")
    created.append("index.md")

    # 7. AI-Sessions 폴더 뼈대
    for sub in ("raw", "wiki/sources", "wiki/concepts", "wiki/decisions", "wiki/errors", "wiki/projects"):
        os.makedirs(os.path.join(target_dir, "AI-Sessions", sub), exist_ok=True)

    return created
