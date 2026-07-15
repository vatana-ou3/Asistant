from __future__ import annotations

import urllib.parse
import webbrowser

from assistant.models import ActionResult, Intent


class BrowserActions:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def open_website(self, intent: Intent) -> ActionResult:
        url = intent.parameters.get("url")
        if not url:
            return ActionResult(False, "No website URL was configured.")
        if self.dry_run:
            return ActionResult(True, f"Would open {url}.")
        webbrowser.open(url)
        return ActionResult(True, f"Opening {intent.target}.")

    def search_web(self, intent: Intent) -> ActionResult:
        query = intent.parameters.get("query", "")
        encoded = urllib.parse.quote_plus(query)
        if intent.target == "youtube":
            url = f"https://www.youtube.com/results?search_query={encoded}"
        else:
            url = f"https://www.google.com/search?q={encoded}"

        if self.dry_run:
            return ActionResult(True, f"Would search {intent.target} for '{query}'.")
        webbrowser.open(url)
        return ActionResult(True, f"Searching {intent.target} for {query}.")
