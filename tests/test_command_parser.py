from assistant.command_parser import normalize_command


def test_normalize_removes_polite_prefixes() -> None:
    assert normalize_command("Could you open Chrome?") == "open chrome"


def test_normalize_removes_wake_word() -> None:
    assert normalize_command("Hey Nova, paste") == "paste"


def test_normalize_removes_ah_mark_wake_word() -> None:
    assert normalize_command("Hey Ah Mark, paste") == "paste"


def test_normalize_repairs_joined_open_command() -> None:
    assert normalize_command("OpenYouTube") == "open youtube"
