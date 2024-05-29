"""
TTorkApp: Top-level ttork application
"""

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header
from ttork.widgets import TiltStatusTree, K8sResourceTable


class TTorkApp(App):
    """Textual Tilt ORKestrator Application"""

    TITLE = "Textual Tilt ORKestrator (ttork)"
    CSS_PATH = "ttork.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    ttork_config = None

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        with Container():
            yield TiltStatusTree("Projects", id="tree-view")
            yield K8sResourceTable(id="k8s-resource-table")
        yield Footer()

    def on_resize(self, event):
        # Do some calculations to determine the available width
        # for the K8sResourceTable widget.
        krt = self.query(K8sResourceTable)[0]
        tst = self.query(TiltStatusTree)[0]
        available_width = self.size.width - tst.size.width - 15
        krt.set_data(available_width=available_width)
