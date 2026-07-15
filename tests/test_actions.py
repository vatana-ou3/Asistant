from actions.browser_actions import BrowserActions
from assistant.models import Intent


def test_browser_search_dry_run() -> None:
    result = BrowserActions(dry_run=True).search_web(
        Intent(action="search_web", target="google", parameters={"query": "FastAPI tutorials"})
    )
    assert result.success
    assert "FastAPI tutorials" in result.message
