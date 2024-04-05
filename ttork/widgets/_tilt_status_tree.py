import requests
from rich.text import Text
import copy

from textual.widgets.tree import TreeNode
from textual.widgets import Tree


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
    #
    # Tree gets updated any time project_info changes
    #
    # TODO: Initialization will come from yaml.config
    pinfo = {
        "/Users/awaller/waller_dev/projects/rcwl/seeder/Tiltfile": dict(
            name="Seeder",
            uiResources=[],
            service_online=False,
            port=10350,
        ),
        "/Users/awaller/waller_dev/projects/rcwl/feeder/Tiltfile": dict(
            name="Feeder",
            uiResources=[],
            service_online=False,
            port=10351,
        ),
    }

    def on_mount(self) -> None:
        self.update_pinfo()
        self.set_interval(1, self.update_pinfo)

    # This behaves as a combined watcher and updater
    def update_pinfo(self) -> None:
        pinfo_old = copy.deepcopy(self.pinfo)
        for pkey in self.pinfo:
            status_json = self.get_tilt_status(self.pinfo[pkey]['port'])
            if status_json:
                self.pinfo[pkey]["uiResources"] = status_json[
                    "uiResources"]
                self.pinfo[pkey]["service_online"] = True
                self.log.debug(
                    'update_pinfo: got tilt status response: ', pkey,
                    'online: ', self.pinfo[pkey]["service_online"],
                )
            else:
                self.log.debug('update_pinfo: no response: ', pkey)
                self.pinfo[pkey]["uiResources"].clear()
                self.pinfo[pkey]["service_online"] = False

        # Reactive watch_(attribute) doesn't work for our dictionary, as the
        # reactive system is doing simple comparisons on the values, which
        # always are equivilant with our dictionary structure.
        #
        # The key here is that pinfo_old was initialized using the deepcopy
        # method, and now the comparison will properly show if any key has
        # been changed.
        if pinfo_old != self.pinfo:
            self.log.debug('TiltStatusTree: Detected data changes, updating.')
            self.clear()
            self.add_treedata(self.root, self.pinfo)
            self.root.expand()

    def get_tilt_status(self, port: int) -> dict:
        """Get the Tilt Status from the running tilt instance, specified
        by port.
        """
        tilt_url = f"http://localhost:{port}/api/view"

        try:
            response = requests.get(tilt_url)

            # Check the response status code
            if response.status_code == 200:
                # The request was successful
                json_response = response.json()
            else:
                # The request failed
                self.log.error(
                    "Error querying tilt status: {}".format(
                        response.status_code,
                    )
                )

            return json_response
        except Exception:
            return None

    def add_treedata(self, root: TreeNode, project_data: object) -> None:
        """Add data to a node"""

        self.log.event('add_treedata called')

        def proper_add_node(node: TreeNode, data: object) -> None:
            """Add a properly formatted node to the tree display for the
            project.
            """
            for project_key in data:
                project_node = root.add("")
                project_node.expand()
                project_pending = False
                project_ok = True
                for resource in data[project_key]['uiResources']:
                    resource_node = project_node.add("")
                    resource_node.allow_expand = False
                    update_status = resource['status']['updateStatus']
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

                # Set the top-level status for the project based on resource
                # status.
                if not data[project_key]["service_online"]:
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
                        f" {data[project_key]["name"]}"
                    ),
                )
                project_node.set_label(project_label)

        proper_add_node(root, project_data)
