import copy
import logging
from kubernetes import config

from ttork.models import K8sDeployments, K8sPods, K8sContainers


class K8sService:
    """Query and maintain status of the k8s cluster resources."""

    def __init__(self, app_config: dict, logger: logging.Logger) -> None:
        self.log = logger
        self.app_config = app_config
        self.context = app_config["k8s"].get("context", "undefined")
        self.namespace = app_config["k8s"].get("namespace", "default")
        self.kube_config = config.load_kube_config(context=self.context)

        self.resources = {
            "Deployments": K8sDeployments(namespace=self.namespace),
            "Pods": K8sPods(namespace=self.namespace),
            "Containers": K8sContainers(namespace=self.namespace),
        }

    def update_cluster_status(self) -> None:
        """Update the status of the cluster resources."""
        for resource in self.resources.values():
            resource.refresh_resource_data()

    def get_k8s_data(self):
        """Return the current k8s resource status data."""
        return copy.deepcopy(self.resources)

    def set_label_selector(
        self, resource_name: str, label_selector: str
    ) -> None:
        """Set the label selector for the specified resource."""
        self.resources[resource_name].label_selector = label_selector

    def clear_label_selector(self, resource_name: str) -> None:
        """Clear the label selector for the specified resource."""
        self.resources[resource_name].label_selector = None

    def get_label_selector(self, resource_name: str) -> str:
        """Get the label selector for the specified resource."""
        return self.resources[resource_name].label_selector
