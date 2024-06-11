from textual.binding import _Bindings


class K8sResourceData:
    """K8sResourceData is a class that holds the data for a
    K8sResourceTable widget.
    """

    def __init__(self, name, namespace, col_meta: list, data: list, **kwargs):
        self.name = name
        self.namespace = namespace
        self.col_names = []
        self.col_min_widths = []
        self.col_alignments = []
        self.bindings = kwargs.get("bindings", _Bindings())
        self.selector = kwargs.get("selector", None)

        # List of column indices that have dynamic widths
        self.dynamic_columns = []

        for index, meta in enumerate(col_meta):
            # Column Name
            name = meta.get("name", "")
            self.col_names.append(name)

            # Column Width
            width = meta.get("width", None)
            if width is None:
                self.col_min_widths.append(len(name))
                self.dynamic_columns.append(index)
            elif width < len(name):
                # Ensure the column width is at least as wide as the name
                self.col_min_widths.append(len(name))
            else:
                self.col_min_widths.append(width)

            # Column Alignments (default to left if not specified)
            self.col_alignments.append(meta.get("align", "left"))

        # Data for the table
        self.data = data

    def __iter__(self):
        for row in self.data:
            yield row

    def __len__(self):
        return len(self.data)
