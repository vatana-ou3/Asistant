from assistant.intent_detector import IntentDetector


def detector() -> IntentDetector:
    return IntentDetector(
        {
            "websites": {"youtube": "https://www.youtube.com"},
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


def test_detect_keyboard_shortcut() -> None:
    intent = detector().detect("next tab")
    assert intent.action == "keyboard_shortcut"
    assert intent.parameters["keys"] == ["ctrl", "tab"]
