import copy
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import DataTable
from textual.binding import _Bindings
from textual.message import Message
from ttork.network import K8sService
from ._confirmation_dialog import ConfirmationDialog

KRT_STYLE_MAP = {
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "loading": "green",
    "terminating": "magenta",
}


class K8sResourceTable(DataTable):
    """K8sResourceTable is a DataTable that displays a list of Kubernetes
    resources.
    """

    base_bindings = _Bindings()
    BINDINGS = [
        ("escape", "show_previous", "Previous"),
    ]

    class DeleteResource(Message):
        """DeleteResource is a Message that triggers a resource deletion"""

        def __init__(self, resource_type: str, identifier: str) -> None:
            self.identifier = identifier
            self.resource_type = resource_type
            self.bubble = True
            super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the K8sResourceTable."""
        yield from super().compose()
        yield ConfirmationDialog(
            "Confirm Delete? Y/n", id="k8s-resource-table-confirmation"
        )

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.k8s_service = K8sService(self.app.ttork_config, self.log)
        self.k8s_service.update_cluster_status()
        self.resource_view = "Deployments"
        self.crumbs = ["Deployments"]
        self.available_width = 0
        self.update_cinfo(force_refresh=True)
        self.set_interval(2, self.update_cinfo)
        self.base_bindings = self._merged_bindings.copy()

    def update_cinfo(
        self,
        force_refresh=False,
        reset_cursor=False,
        show_view=None,
        label_selector=None,
    ) -> None:
        """Update the cluster status information."""
        k8s_data_old = self.k8s_service.get_k8s_data()

        # Set the view
        if show_view:
            tmp_view = copy.copy(self.resource_view)
            self.resource_view = show_view
            self.previous_view = tmp_view

        # Apply label_selector, if defined (will persist across updates)
        if label_selector:
            self.k8s_service.set_label_selector(
                self.resource_view, label_selector
            )

        # Update the cluster status
        self.k8s_service.update_cluster_status()

        if reset_cursor:
            self.move_cursor(row=0)

        if k8s_data_old != self.k8s_service.get_k8s_data() or force_refresh:
            self.set_data()

    def set_border_title(self) -> None:
        """Set the border title for the K8sResourceTable."""
        resource_data = self.k8s_service.resources[
            self.resource_view
        ].get_resource_data()

        selected = self.k8s_service.get_label_selector(self.resource_view)

        self.border_title = Text.assemble(
            resource_data.name,
            (f"({resource_data.namespace})", "blue"),
            (f"[{len(resource_data)}]", "green"),
            (f"<{selected}>", "orange") if selected else "",
        )

    def set_data(self, available_width: int = 0):
        """Set the data for the K8sResourceTable."""

        # Save the current cursor position (highlighted row)
        current_cursor = self.cursor_row

        # Clear existing values
        self.clear(True)
        self.clear_cached_dimensions()
        self.log.debug(f"Available Width: {available_width}")

        # If specified, persist available_width for future updates
        if available_width > 0:
            self.available_width = available_width

        # Get resource data for the current view
        resource_data = self.k8s_service.resources[
            self.resource_view
        ].get_resource_data()

        # Dynamically update the key bindings to be resource type specific
        if resource_data.bindings:
            self._bindings = self._bindings.merge(
                [self.base_bindings, resource_data.bindings]
            )
            self.refresh_bindings()

        self.set_border_title()

        # Get the minimum table content width
        self.min_table_width = sum(resource_data.col_min_widths)

        # Get number of dynamic columns
        self.num_dynamic_cols = len(resource_data.dynamic_columns)

        # Calculate extra padding if table is wider than content
        if self.available_width > self.min_table_width:
            dynamic_padding = (
                (self.available_width - self.min_table_width)
                // self.num_dynamic_cols
            ) - 1
        else:
            dynamic_padding = 0

        # Set Column Headers
        for index, col_name, col_min_width in zip(
            range(len(resource_data.col_names)),
            resource_data.col_names,
            resource_data.col_min_widths,
        ):
            if index in resource_data.dynamic_columns:
                width = col_min_width + dynamic_padding
            else:
                width = col_min_width
            self.add_column(col_name, width=width)

        # Style rows individually based on values
        for row in resource_data:
            styled_row = []
            for index, cell in enumerate(row["values"]):
                styled_row.append(
                    Text(
                        cell,
                        style=KRT_STYLE_MAP.get(
                            row.get("style", "info"),
                        ),
                        justify=resource_data.col_alignments[index],
                    )
                )
            self.add_row(*styled_row)

        # Restore the cursor position (highlighted row)
        self.move_cursor(row=current_cursor)

    def action_select_row(self, view: str) -> None:
        """Generic select resource action for table.

        Specific implementation is provided in the bindings for each
        K8sResourceData instance.
        """
        selected_row = self.get_row_at(self.cursor_row)
        valid_views = [str(s) for s in self.k8s_service.resources.keys()]

        # Logs is a valid view, but does not have a resource associated with it
        valid_views.append("Logs")
        if selected_row is not None and view in valid_views:
            current_view = self.crumbs[-1]
            selector = (
                self.k8s_service.resources[current_view]
                .get_resource_data()
                .selector
            )

            # Show the logs for the selected container
            if view == "Logs":
                pod_name = self.k8s_service.resources["Containers"].pod_name
                self.app.query_one("#logs-display").show(
                    pod_name, str(selected_row[0])
                )
                return

            self.crumbs.append(view)

            # Apply label_selector, if defined by parent view
            if selector:
                label_selector = "{0}{1}".format(
                    selector["label"], selected_row[selector["index"]]
                )
            else:
                label_selector = None

            self.update_cinfo(
                force_refresh=True,
                reset_cursor=True,
                show_view=view,
                label_selector=label_selector,
            )

    def action_show_previous(self) -> None:
        """Show the previous resource type in the table."""
        if len(self.crumbs) == 1:
            return

        # Clear any label selector for the current view when exiting the view
        current_view = self.crumbs.pop()
        self.k8s_service.clear_label_selector(current_view)

        previous = self.crumbs[-1]
        self.update_cinfo(
            force_refresh=True, reset_cursor=True, show_view=previous
        )

    def action_show_description(self) -> None:
        """Show the description of the selected resource."""
        selected_row = self.get_row_at(self.cursor_row)
        if selected_row is not None:
            description = self.k8s_service.resources[
                self.resource_view
            ].get_description(str(selected_row[0]))

            if description:
                info = self.app.query_one("#info-box")
                info.text = description
                info.visible = True
                info.focus()

    def action_delete_resource(self) -> None:
        """Delete the selected resource."""
        selected_row = self.get_row_at(self.cursor_row)
        if selected_row is not None:
            confirmation = self.app.query_one(
                "#k8s-resource-table-confirmation"
            )

            # Show confirmation dialog, and pass it the appropriate message
            # to use if the user confirms the action.
            confirmation.show(
                "Confirm Delete? Y/n",
                self.DeleteResource(self.resource_view, str(selected_row[0])),
            )

    def on_k8s_resource_table_delete_resource(
        self, message: DeleteResource
    ) -> None:
        """Handle the deletion of a resource."""
        if hasattr(
            self.k8s_service.resources[message.resource_type],
            "delete_resource",
        ):
            self.k8s_service.resources[message.resource_type].delete_resource(
                message.identifier
            )

    def action_resource_call(self, action: str) -> None:
        """Dynamic method for calling resource defined methods.

        Call the specified method on the selected resource, passing it
        the app and the selected row data.
        """
        selected_row = self.get_row_at(self.cursor_row)
        if selected_row is not None:
            getattr(
                self.k8s_service.resources[self.resource_view],
                action,
            )(self.app, selected_row)

    def reset_view(self) -> None:
        """Reset the view to the initial state."""
        self.resource_view = "Deployments"
        self.crumbs = ["Deployments"]
        self.update_cinfo(force_refresh=True, reset_cursor=True)
