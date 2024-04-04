"""
TTorkApp: Top-level ttork application
"""
import requests

from rich.text import Text

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Static, Tree
from textual.widgets.tree import TreeNode


TILT_STATUS_ICONS = dict(
    ok=Text.from_markup(":green_circle:"),
    pending=Text.from_markup(":orange_circle:", style="blink"),
    none=Text.from_markup(":black_circle:"),
    in_progress=Text.from_markup(":blue_circle:", style="blink"),
    error=Text.from_markup(":red_circle:"),
    offline=Text.from_markup(":black_circle: (offline)"),
    other=Text.from_markup(":purple_circle:"),
)


class TTorkApp(App):
    """Textual Tilt ORKestration App
    """

    CSS_PATH = "ttork.tcss"
    BINDINGS = [
        ("c", "clear", "Clear"),
        ("q", "quit", "Quit"),
    ]

    # This will be read in from the yaml config file
    project_info = {
        # In yaml, this will be relative: 'seeder/Tiltfile', we will
        # convert on initial load of yaml file based on cwd to absolute.
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

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header()
        with Container():
            yield Tree("Root", id="tree-view")
            with VerticalScroll(id="code-view"):
                yield Static(id="code", expand=True)
        yield Footer()

    @classmethod
    def add_treedata(cls, root: TreeNode, project_data: object) -> None:
        """Add data to a node"""

        def proper_add_node(node: TreeNode, data: object) -> None:
            """Add a properly formatted node to the tree display for the
            project.

            Args:
                node (TreeNode): _description_
                data (object): _description_
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

    # format this
    def on_mount(self) -> None:
        # Query the project info, if available
        for pkey in self.project_info:
            status_json = self.get_tilt_status(self.project_info[pkey]['port'])
            if status_json:
                self.project_info[pkey]["uiResources"] = status_json[
                    "uiResources"]
                self.project_info[pkey]["service_online"] = True
            else:
                self.project_info[pkey]["uiResources"].clear()
                self.project_info[pkey]["service_online"] = False

        # Set the tree nodes for all projects
        tree = self.query_one(Tree)
        tree.root.set_label("Projects")
        self.add_treedata(tree.root, self.project_info)
        tree.root.expand()

    def action_clear(self) -> None:
        """Clear the tree (remove all nodes)."""
        tree = self.query_one(Tree)
        tree.clear()

    def get_tilt_status(self, port: int) -> dict:
        tilt_url = f"http://localhost:{port}/api/view"

        try:
            response = requests.get(tilt_url)

            # Check the response status code
            if response.status_code == 200:
                # The request was successful
                json_response = response.json()
            else:
                # The request failed
                print(
                    "Error querying tilt status: {}".format(
                        response.status_code,
                    )
                )

            return json_response
        except Exception:
            return None
