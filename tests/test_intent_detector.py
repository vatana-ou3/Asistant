from assistant.intent_detector import IntentDetector


def detector() -> IntentDetector:
    return IntentDetector(
        {
            "websites": {"youtube": "https://www.youtube.com"},
            "applications": {
                "team": "ms-teams",
                "folder": "explorer",
                "vs code": "code",
                "screenshot": "snippingtool",
                "snipping tool": "snippingtool",
            },
            "keyboard_shortcuts": {"copy": ["ctrl", "c"], "next tab": ["ctrl", "tab"]},
        }
    )


def test_detect_open_application() -> None:
    intent = detector().detect("Launch Telegram")
    assert intent.action == "open_application"
    assert intent.target == "telegram"


def test_detect_set_volume() -> None:
    intent = detector().detect("set volume to 75 percent")
    assert intent.action == "set_volume"
    assert intent.parameters["level"] == 75


def test_detect_youtube_search() -> None:
    intent = detector().detect("Search YouTube for Python tutorials")
    assert intent.action == "search_web"
    assert intent.target == "youtube"
    assert intent.parameters["query"] == "python tutorials"


def test_detect_natural_youtube_search() -> None:
    intent = detector().detect("Can you open YouTube for me and search for Python?")
    assert intent.action == "search_web"
    assert intent.target == "youtube"
    assert intent.parameters["query"] == "python"


def test_detect_youtube_search_with_site_at_end() -> None:
    intent = detector().detect("Search for Python tutorials on YouTube")
    assert intent.action == "search_web"
    assert intent.target == "youtube"
    assert intent.parameters["query"] == "python tutorials"


def test_detect_keyboard_shortcut() -> None:
    intent = detector().detect("next tab")
    assert intent.action == "keyboard_shortcut"
    assert intent.parameters["keys"] == ["ctrl", "tab"]


def test_detect_bare_application_alias() -> None:
    intent = detector().detect("team")
    assert intent.action == "open_application"
    assert intent.target == "team"


def test_detect_bare_website_name() -> None:
    intent = detector().detect("YouTube")
    assert intent.action == "open_website"
    assert intent.target == "youtube"


def test_detect_take_screenshot_opens_snipping_tool() -> None:
    intent = detector().detect("Take a screenshot")
    assert intent.action == "open_application"
    assert intent.target == "snipping tool"
