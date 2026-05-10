import os
from pytest import fail
import subprocess
import sys


def test_type_checker_reports_no_errors() -> None:
    try:
        subprocess.check_output(
            ["mypy"],
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        fail("Typechecker failed with output:\n\n%s" % e.output.rstrip(), pytrace=False)


def test_imports_are_sorted() -> None:
    try:
        subprocess.check_output(
            ["isort", "--check-only", "src/gvc"],
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        fail("isort found unsorted imports:\n\n%s" % e.output.rstrip(), pytrace=False)


def test_that_zizmor_reports_no_github_action_workflow_vulnerabilities() -> None:
    zizmor = os.path.join(os.path.dirname(sys.executable), "zizmor")
    try:
        subprocess.check_output(
            [zizmor, "--persona", "auditor", ".github/workflows/"],
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )
    except subprocess.CalledProcessError as e:
        fail("zizmor found vulnerabilities:\n\n%s" % e.output.rstrip(), pytrace=False)
