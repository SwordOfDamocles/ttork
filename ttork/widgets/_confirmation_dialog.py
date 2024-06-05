from textual.widgets import TextArea
from textual.message import Message


class ConfirmationDialog(TextArea):
    """ConfirmationDialog is a Static widget that displays a confirmation
    dialog.
    """

    BINDINGS = [
        ("y", "confirm", "Yes"),
        ("n", "cancel", "No"),
    ]

    def on_mount(self) -> None:
        self.visible = False
        self.read_only = True

    def show(self, text: str, message: Message = None) -> None:
        """Show the confirmation dialog."""
        self.text = text
        self.move_cursor((0, len(self.text)), select=False)
        self.visible = True
        self.message = message
        self.focus()

    def hide(self) -> None:
        """Hide the confirmation dialog."""
        self.visible = False
        self.app.query_one("#k8s-resource-table").focus()

    def action_confirm(self) -> None:
        """Confirm the action."""
        self.post_message(self.message)
        self.hide()

    def action_cancel(self) -> None:
        """Cancel the action."""
        self.hide()
