import copy
import logging
from kubernetes import config

from ttork.models import K8sData, get_deployments, get_pods


class K8sService:
    """Query and maintain status of the k8s cluster resources."""

    def __init__(self, app_config: dict, logger: logging.Logger) -> None:
        self.k8s_data = K8sData()
        self.log = logger
        self.app_config = app_config
        self.context = app_config["k8s"].get("context", "undefined")
        self.namespace = app_config["k8s"].get("namespace", "default")
        self.kube_config = config.load_kube_config(context=self.context)

        self.resources = {
            "Deployments": {
                "name": "Deployments",
                "namespace": self.namespace,
                "function": get_deployments,
                "label_selector": None,
            },
            "Pods": {
                "name": "Pods",
                "namespace": self.namespace,
                "function": get_pods,
                "label_selector": None,
            },
        }

    def update_cluster_status(self) -> None:
        """Update the status of the cluster resources."""
        for resource in self.resources.values():
            self.k8s_data[resource["name"]] = resource["function"](
                namespace=resource["namespace"],
                label_selector=resource["label_selector"],
            )

    def get_k8s_data(self) -> K8sData:
        """Return the K8sData object."""
        return copy.deepcopy(self.k8s_data)

    def set_label_selector(
        self, resource_name: str, label_selector: str
    ) -> None:
        """Set the label selector for the specified resource."""
        self.resources[resource_name]["label_selector"] = label_selector

    def clear_label_selector(self, resource_name: str) -> None:
        """Clear the label selector for the specified resource."""
        self.resources[resource_name]["label_selector"] = None
