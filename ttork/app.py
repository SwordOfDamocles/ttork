"""
TTorkApp: Top-level ttork application
"""

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Static
from ttork.widgets import TiltStatusTree


class TTorkApp(App):
    """Textual Tilt ORKestrator Application"""

    TITLE = "Textual Tilt ORKestrator"
    CSS_PATH = "ttork.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        with Container():
            yield TiltStatusTree("Projects", id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
        yield Footer()
