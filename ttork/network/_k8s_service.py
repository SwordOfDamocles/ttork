import copy
import logging
from datetime import datetime, timezone
from kubernetes import client, config

from ttork.models import K8sData, K8sResourceData


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
        self.k8s_data["Deployments"] = self.get_deployments()
        self.k8s_data["Pods"] = self.get_pods()

    def get_k8s_data(self) -> K8sData:
        """Return the K8sData object."""
        return copy.deepcopy(self.k8s_data)

    def get_deployments(self) -> K8sResourceData:
        """Get the Deployment resources from the cluster."""
        api_instance = client.AppsV1Api()
        deployments = api_instance.list_namespaced_deployment(
            namespace=self.namespace
        )
        deployment_data = []
        now = datetime.now(timezone.utc)
        for deployment in deployments.items:
            delta = now - deployment.metadata.creation_timestamp
            days = delta.seconds // 86400
            minutes = (delta.seconds - days * 86400) // 60
            seconds = delta.seconds - (days * 86400) - (minutes * 60)
            deployment_data.append(
                {
                    "values": [
                        deployment.metadata.name,
                        f"{deployment.status.ready_replicas}/{deployment.status.replicas}",
                        str(deployment.status.replicas),
                        str(deployment.status.available_replicas),
                        deployment.metadata.namespace,
                        f"{days:02}d:{minutes:02}m:{seconds:02}s",
                    ],
                    "style": "info",
                }
            )
        return K8sResourceData(
            name="Deployments",
            namespace=self.namespace,
            col_meta=[
                {"name": "NAME", "width": None, "align": "left"},
                {"name": "READY", "width": 10, "align": "center"},
                {"name": "CURRENT", "width": 10, "align": "center"},
                {"name": "AVAILABLE", "width": 10, "align": "center"},
                {"name": "NAMESPACE", "width": None, "align": "left"},
                {"name": "AGE", "width": 15, "align": "left"},
            ],
            data=deployment_data,
        )

    def get_pods(self) -> K8sResourceData:
        """Get the Pod resources from the cluster."""
        api_instance = client.CoreV1Api()
        pods = api_instance.list_namespaced_pod(namespace=self.namespace)
        pod_data = []
        now = datetime.now(timezone.utc)
        for pod in pods.items:
            delta = now - pod.metadata.creation_timestamp
            days = delta.seconds // 86400
            minutes = (delta.seconds - days * 86400) // 60
            seconds = delta.seconds - (days * 86400) - (minutes * 60)
            pod_data.append(
                {
                    "values": [
                        pod.metadata.name,
                        pod.status.phase,
                        pod.status.pod_ip,
                        pod.metadata.namespace,
                        f"{days:02}d:{minutes:02}m:{seconds:02}s",
                    ],
                    "style": "info",
                }
            )
        return K8sResourceData(
            name="Pods",
            namespace=self.namespace,
            col_meta=[
                {"name": "NAME", "width": None, "align": "left"},
                {"name": "STATUS", "width": 10, "align": "center"},
                {"name": "IP", "width": 15, "align": "center"},
                {"name": "NAMESPACE", "width": None, "align": "left"},
                {"name": "AGE", "width": 15, "align": "left"},
            ],
            data=pod_data,
        )
