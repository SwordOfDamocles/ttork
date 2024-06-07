from textual.widgets import Log


class ContainerLogs(Log):
    """Shows logs for a given container."""

    BINDINGS = [
        ("escape", "close_logs", "Back to Containers"),
    ]

    def on_mount(self) -> None:
        self.visible = False
        self.pod_name = ""
        self.container_name = ""
        self.set_interval(2, self.update_loginfo)

    def show(self, pod_name: str, container_name: str) -> None:
        """Show the confirmation dialog."""
        self.visible = True
        self.pod_name = pod_name
        self.container_name = container_name
        self.log.debug(f"Showing logs for {container_name} in {pod_name}.")
        self.update_loginfo()
        self.focus()

    def hide(self) -> None:
        """Hide the confirmation dialog."""
        self.visible = False
        self.pod_name = ""
        self.container_name = ""
        self.app.query_one("#k8s-resource-table").focus()
        self.clear()

    def update_loginfo(self) -> None:
        if self.visible and self.pod_name and self.container_name:
            log_data = (
                self.app.query_one("#k8s-resource-table")
                .k8s_service.resources["Containers"]
                .get_container_logs(self.container_name, self.pod_name)
            )
            self.clear()
            if log_data:
                self.write(log_data, scroll_end=True)
            else:
                self.write("No logs available.", scroll_end=True)

    def action_close_logs(self) -> None:
        """Close the logs display."""
        self.hide()
