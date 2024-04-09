from rich.text import Text
from textual.widgets import Tree
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
    ]

    def on_mount(self) -> None:
        self.tilt_service = TiltService(self.app.ttork_config, self.log)
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
        """Clear and re-create all the tree nodes, based on self.pinfo
        """
        self.log.debug('TiltStatusTree: Detected data changes, updating.')
        self.clear()
        self.add_treedata()
        self.root.expand()

    def action_start_tilt(self) -> None:
        """Start the Tilt services."""
        self.tilt_service.start_all_tilt()
        # self.update_pinfo(force_refresh=True)

    def action_teardown_tilt(self) -> None:
        """Tear down the Tilt services."""
        self.tilt_service.tear_down_all_resources()
        # self.update_pinfo(force_refresh=True)

    def add_treedata(self) -> None:
        """Add a properly formatted node to the tree display for the
        projects in the self.pinfo data struct.
        """
        pinfo = self.tilt_service.get_status_info()
        for project_key in pinfo:
            project_node = self.root.add("")
            project_node.expand()
            project_pending = False
            project_ok = True
            for resource in pinfo[project_key]['uiResources']:
                resource_node = project_node.add("")
                resource_node.allow_expand = False
                update_status = resource['status'].get(
                    'updateStatus', 'offline')
                label = Text.assemble(
                    TILT_STATUS_ICONS.get(
                        update_status,
                        TILT_STATUS_ICONS['other'],
                    ),
                    Text.from_markup(
                        f" [b]{resource['metadata']['name']}[/b]"
                    ),
                )
                resource_node.set_label(label)

                if (
                    update_status == 'pending'
                    or update_status == 'in_progress'
                ):
                    project_pending = True
                elif update_status == 'error':
                    project_ok = False

            # Set the top-level status based on combined resource states
            if not pinfo[project_key]["service_online"]:
                ps_icon = TILT_STATUS_ICONS['offline']
            elif project_pending:
                ps_icon = TILT_STATUS_ICONS['pending']
            elif not project_ok:
                ps_icon = TILT_STATUS_ICONS['error']
            else:
                ps_icon = TILT_STATUS_ICONS['ok']
            project_label = Text.assemble(
                ps_icon,
                Text.from_markup(
                    f" {pinfo[project_key]["name"]}"
                ),
            )
            project_node.set_label(project_label)
