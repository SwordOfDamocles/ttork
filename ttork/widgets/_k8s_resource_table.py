from textual.widgets import DataTable
from ttork.models import K8sData
from rich.text import Text
from ttork.network import K8sService

KRT_STYLE_MAP = {
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "loading": "purple",
}


class K8sResourceTable(DataTable):
    """K8sResourceTable is a DataTable that displays a list of Kubernetes
    resources.
    """

    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.zebra_stripes = True
        self.k8s_service = K8sService(self.app.ttork_config, self.log)
        self.k8s_service.update_cluster_status()
        self.resource_view = "Deployments"
        self.available_width = 0
        self.update_cinfo(force_refresh=True)
        self.set_interval(1, self.update_cinfo)

    def update_cinfo(self, force_refresh=False) -> None:
        """Update the cluster status information."""
        k8s_data_old = self.k8s_service.get_k8s_data()
        self.k8s_service.update_cluster_status()

        if k8s_data_old != self.k8s_service.get_k8s_data() or force_refresh:
            self.set_data()

    def set_data(self, available_width: int = 0):
        # Set the initial data and columns
        self.clear(True)
        self.clear_cached_dimensions()
        self.log.debug(f"Available Width: {available_width}")

        # If specified, persist available_width for future updates
        if available_width > 0:
            self.available_width = available_width

        # Get resource data for the current view
        resource_data = self.k8s_service.k8s_data[self.resource_view]

        # I think we'll have to have a function to set this
        self.border_title = Text.assemble(
            resource_data.name,
            (f"({resource_data.namespace})", "blue"),
            (f"[{len(resource_data)}]", "green"),
        )

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
