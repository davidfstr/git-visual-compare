import gvc
from harness.app import GvcApp
from harness.diff_fixture import DiffFixture
from pathlib import Path
import tomllib


def test_given_about_panel_visible_then_shows_full_and_short_app_name(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)

    texts = gvc_app.show_about_panel_and_list_texts()
    assert "Git Visual Compare (gvc)" in texts


# TODO: Consider moving this test to a new/better module.
#       Is only tangentally related to the About Panel.
def test_version_numbers_consistent_everywhere() -> None:
    init_version = gvc.__version__
    
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)
    pyproject_version = pyproject_data["project"]["version"]

    assert init_version == pyproject_version, 'gvc/__init__.py and pyproject.toml report inconsistent versions'