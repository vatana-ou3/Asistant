from assistant.command_parser import normalize_command


def test_normalize_removes_polite_prefixes() -> None:
    assert normalize_command("Could you open Chrome?") == "open chrome"


def test_normalize_removes_wake_word() -> None:
    assert normalize_command("Hey Nova, paste") == "paste"
