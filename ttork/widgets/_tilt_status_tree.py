import webbrowser
from rich.text import Text
from textual.widgets import Tree
from textual import events
from ttork.network import TiltService


TILT_STATUS_ICONS = dict(
    ok=Text.from_markup(":green_circle:"),
    pending=Text.from_markup(":orange_circle:", style="blink"),
    none=Text.from_markup(":black_circle:"),
    in_progress=Text.from_markup(":blue_circle:", style="blink"),
    error=Text.from_markup(":red_circle:"),
    offline=Text.from_markup(":black_circle: (offline)"),
    other=Text.from_markup(":purple_circle:"),
)


class TiltStatusTree(Tree):
    """TiltStatusTree tracks and displays the status of running
    Tilt.dev services.
    """

    BINDINGS = [
        ("s", "start_tilt", "Start Tilt"),
        ("t", "teardown_tilt", "Tear Down Tilt"),
        ("space", "open_tilt_ui", "Open Tilt UI"),
    ]

    def on_mount(self) -> None:
        self.border_title = "Tilt Services"
        self.tilt_service = TiltService(self.app.ttork_config, self.log)

        if self.app.ttork_config.get("autostart", False):
            self.tilt_service.start_tilt_processes()

        self.update_pinfo(force_refresh=True)
        self.set_interval(1, self.update_pinfo)

    def update_pinfo(self, force_refresh=False) -> None:
        """Update the Tilt service statuses inside of the pinfo structure.

        This acts as both a watcher and updater, as we can't use the standard
        Textual paradigm of reactive attributes with our dict[dict] struct.
        """
        status_info_old = self.tilt_service.get_status_info()
        self.tilt_service.update_status_info()

        if (
            status_info_old != self.tilt_service.get_status_info()
            or force_refresh
        ):
            self.refresh_tree_view()

    def refresh_tree_view(self) -> None:
        """Clear and re-create all the tree nodes, based on self.pinfo"""
        self.log.debug("TiltStatusTree: Detected data changes, updating.")
        self.clear()
        self.add_treedata()
        self.root.expand()

    def action_start_tilt(self) -> None:
        """Start the Tilt services."""
        self.tilt_service.start_tilt_processes()

    def action_teardown_tilt(self) -> None:
        """Tear down the Tilt services."""
        self.app.query_one("#k8s-resource-table").reset_view()
        self.tilt_service.tear_down_all_resources()

    def action_open_tilt_ui(self) -> None:
        """Open the Tilt UI in the browser."""
        selected_node = self.cursor_node
        if selected_node.data:
            webbrowser.open_new_tab(
                "http://localhost:{0}/r/(all)/overview".format(
                    selected_node.data["port"],
                )
            )

    def check_action(
        self,
        action: str,
        parameters: tuple[object, ...],
    ) -> bool:
        """Check if the action is allowed."""
        if action == "open_tilt_ui":
            # Disable if the tilt service is shown as offline
            selected_node = self.cursor_node
            if selected_node.data:
                return selected_node.data["online"]
            else:
                return False
        return True

    def add_treedata(self) -> None:
        """Add a properly formatted node to the tree display for the
        projects in the self.pinfo data struct.
        """
        pinfo = self.tilt_service.get_status_info()
        for project_key in pinfo:
            p_node_data = {
                "key": project_key,
                "name": pinfo[project_key]["name"],
                "port": pinfo[project_key]["port"],
                "online": pinfo[project_key]["service_online"],
            }
            project_node = self.root.add("", data=p_node_data)
            project_node.expand()
            project_pending = False
            project_ok = True
            for resource in pinfo[project_key]["uiResources"]:
                resource_node = project_node.add("", data=p_node_data)
                resource_node.allow_expand = False
                update_status = resource["status"].get(
                    "updateStatus", "offline"
                )
                label = Text.assemble(
                    TILT_STATUS_ICONS.get(
                        update_status,
                        TILT_STATUS_ICONS["other"],
                    ),
                    Text.from_markup(
                        f" [b]{resource['metadata']['name']}[/b]",
                    ),
                )
                resource_node.set_label(label)

                if (
                    update_status == "pending"
                    or update_status == "in_progress"
                ):
                    project_pending = True
                elif update_status == "error":
                    project_ok = False

            # Set the top-level status based on combined resource states
            if not pinfo[project_key]["service_online"]:
                ps_icon = TILT_STATUS_ICONS["offline"]
            elif project_pending:
                ps_icon = TILT_STATUS_ICONS["pending"]
            elif not project_ok:
                ps_icon = TILT_STATUS_ICONS["error"]
            else:
                ps_icon = TILT_STATUS_ICONS["ok"]
            project_label = Text.assemble(
                ps_icon,
                Text.from_markup(f" {pinfo[project_key]['name']}"),
            )
            project_node.set_label(project_label)

    def _on_resize(self, event: events.Resize) -> None:
        super()._on_resize(event)
        self.app.on_resize(event)
