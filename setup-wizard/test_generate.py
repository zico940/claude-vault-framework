import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(__file__))
from generate import generate_vault  # noqa: E402


def test_generate_vault_creates_core_files():
    target = tempfile.mkdtemp()
    try:
        created = generate_vault(
            target_dir=target,
            domain="동네 카페",
            constraints="1인 운영, 외부 고객 데이터 없음",
        )
        assert "CLAUDE.md" in created
        assert ".claude/CLAUDE.md" in created
        assert ".claude/rules/core/file-ops.md" in created
        assert ".claude/rules/core/uncertainty.md" in created
        assert ".claude/rules/core/open-questions.md" in created
        assert ".claude/rules/core/rule-authoring.md" in created
        assert ".claude/skills/verify-docs/check.py" in created
        assert "tasks/questions/open-questions.md" in created

        for d in (
            "AI-Sessions/raw",
            "AI-Sessions/wiki/sources",
            "AI-Sessions/wiki/concepts",
            "AI-Sessions/wiki/decisions",
            "AI-Sessions/wiki/errors",
            "AI-Sessions/wiki/projects",
        ):
            assert os.path.isdir(os.path.join(target, d)), f"{d} 폴더가 생성되지 않음"

        with open(os.path.join(target, "CLAUDE.md"), encoding="utf-8") as f:
            assert "동네 카페" in f.read()

        with open(
            os.path.join(target, ".claude/rules/core/open-questions.md"), encoding="utf-8"
        ) as f:
            content = f.read()
            assert "1인 운영, 외부 고객 데이터 없음" in content
            assert "{{도메인_제약}}" not in content
    finally:
        shutil.rmtree(target, ignore_errors=True)


def test_generate_vault_verify_docs_passes():
    """generate_vault가 만든 vault에서 이식된 check.py가 통과하는지 확인."""
    import subprocess

    target = tempfile.mkdtemp()
    try:
        generate_vault(target_dir=target, domain="법무법인", constraints="비밀유지 의무")
        result = subprocess.run(
            [sys.executable, ".claude/skills/verify-docs/check.py"],
            cwd=target,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "OK" in result.stdout
    finally:
        shutil.rmtree(target, ignore_errors=True)


if __name__ == "__main__":
    test_generate_vault_creates_core_files()
    test_generate_vault_verify_docs_passes()
    print("generate.py 테스트 통과")
