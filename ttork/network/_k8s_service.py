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

    def update_cluster_status(self) -> None:
        """Update the status of the cluster resources."""
        self.k8s_data["Deployments"] = get_deployments(self.namespace)
        self.k8s_data["Pods"] = get_pods(self.namespace)

    def get_k8s_data(self) -> K8sData:
        """Return the K8sData object."""
        return copy.deepcopy(self.k8s_data)
