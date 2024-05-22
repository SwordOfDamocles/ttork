"""
TTorkApp: Top-level ttork application
"""

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Input
from ttork.widgets import TiltStatusTree, K8sResourceTable
from ttork.models import K8sResourceData


KTD_EXAMPLE = K8sResourceData(
    name="Deployments",
    namespace="default",
    col_meta=[
        {"name": "NAME", "width": None, "align": "left"},
        {"name": "READY", "width": 10, "align": "center"},
        {"name": "CURRENT", "width": 10, "align": "center"},
        {"name": "AVAILABLE", "width": 10, "align": "center"},
        {"name": "NAMESPACE", "width": None, "align": "left"},
        {"name": "AGE", "width": 6, "align": "right"},
    ],
    data=[
        {
            "values": ["my-app", "1/1", "1", "1", "default", "2d"],
            "style": "info",
        },
        {
            "values": ["my-app-01", "1/1", "1", "1", "default", "2d"],
            "style": "warning",
        },
        {
            "values": ["my-app-02", "1/1", "1", "1", "default", "2d"],
            "style": "error",
        },
        {
            "values": ["my-app-03", "1/1", "1", "1", "default", "2d"],
            "style": "info",
        },
        {
            "values": ["my-app-04", "1/1", "1", "1", "default", "2d"],
            "style": "warning",
        },
        {
            "values": ["my-app-05", "1/1", "1", "1", "default", "2d"],
            "style": "error",
        },
        {
            "values": ["my-app-06", "1/1", "1", "1", "default", "2d"],
            "style": "loading",
        },
        {
            "values": ["my-app-07", "1/1", "1", "1", "default", "2d"],
            "style": "info",
        },
        {
            "values": ["my-app-08", "1/1", "1", "1", "default", "2d"],
            "style": "info",
        },
        {
            "values": ["my-app-09", "1/1", "1", "1", "default", "2d"],
            "style": "info",
        },
    ],
)


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
            # yield Input(placeholder="Type here to filter the data table")
            yield K8sResourceTable(KTD_EXAMPLE, id="k8s-resource-table")
        yield Footer()

    def on_resize(self, event):
        # Do some calculations to determine the available width for the
        # K8sResourceTable widget.
        krt = self.query(K8sResourceTable)[0]
        tst = self.query(TiltStatusTree)[0]
        available_width = self.size.width - tst.size.width - 15
        krt.set_data(available_width=available_width)
