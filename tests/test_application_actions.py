from actions.application_actions import ApplicationActions


def test_dry_run_does_not_require_path_resolution() -> None:
    actions = ApplicationActions({"chrome": "chrome"}, dry_run=True)
    result = actions.open_application(type("Intent", (), {"target": "chrome"})())
    assert result.success
    assert result.message == "Would open chrome."
