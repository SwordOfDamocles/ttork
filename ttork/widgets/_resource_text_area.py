from textual.widgets import TextArea


class ResourceTextArea(TextArea):
    """ResourceTextArea is a TextArea that displays a Kubernetes resource."""

    BINDINGS = [
        ("escape", "hide_window", "back"),
    ]

    def action_hide_window(self) -> None:
        """Hide the window."""
        self.visible = False
        self.app.query_one("#k8s-resource-table").focus()
