from ttork.models._k8s_resource_data import K8sResourceData


class K8sData:
    """K8sData holds a collection of K8sResourceData objects."""

    def __init__(self):
        self.resources = {}

    def __getitem__(self, key: str) -> K8sResourceData:
        return self.resources[key]

    def __setitem__(self, key: str, value: K8sResourceData):
        self.resources[key] = value
