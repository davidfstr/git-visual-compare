from harness.app import GvcApp
from harness.diff_fixture import DiffFixture


def test_given_about_panel_visible_then_shows_full_and_short_app_name(
    gvc_app: GvcApp,
    diff_fixture: DiffFixture,
) -> None:
    gvc_app.run_cli(diff_fixture.args, cwd=diff_fixture.repo)

    texts = gvc_app.show_about_panel_and_list_texts()
    assert "Git Visual Compare (gvc)" in texts
