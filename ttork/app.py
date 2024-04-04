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
    pending=Text.from_markup(":yellow_circle:", style="blink"),
    none=Text.from_markup(":black_circle:"),
    in_progress=Text.from_markup(":orange_circle:", style="blink"),
    error=Text.from_markup(":red_circle:"),
    other=Text.from_markup(":purple_circle:"),
)


class TTorkApp(App):
    """Textual Tilt ORKestration App"""

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
            name="Seeder", uiResources=[]
        )
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
                label = Text.assemble(
                    TILT_STATUS_ICONS['in_progress'],
                    Text.from_markup(
                        f" {data[project_key]["name"]}"
                    ),
                )
                project_node.set_label(label)
                project_node.expand()
                for resource in data[project_key]['uiResources']:
                    resource_node = project_node.add("")
                    resource_node.allow_expand = False
                    label = Text.assemble(
                        TILT_STATUS_ICONS['ok'],
                        Text.from_markup(
                            f" [b]{resource['metadata']['name']}[/b]"
                        ),
                    )
                    resource_node.set_label(label)

        proper_add_node(root, project_data)

    # format this
    def on_mount(self) -> None:
        status_json = self.get_tilt_status(10350)
        self.project_info[status_json["uiSession"]["status"]["tiltfileKey"]][
            "uiResources"
        ] = status_json["uiResources"]
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
        response = requests.get(tilt_url)

        # Check the response status code
        if response.status_code == 200:
            # The request was successful
            json_response = response.json()
        else:
            # The request failed
            print(
                "Error querying tilt status: {}".format(response.status_code)
            )

        return json_response
