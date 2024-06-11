import yaml
from datetime import datetime, timezone
from kubernetes import client
from kubernetes.client.rest import ApiException
from ttork.utilities import format_age
from ttork.models import K8sResourceData
from textual.binding import Binding, _Bindings


class K8sPods:
    """K8sPods is a model for Kubernetes Pods."""

    def __init__(self, namespace: str) -> None:
        self.name: str = "Pods"
        self.namespace: str = namespace
        self.label_selector: str = None
        self.resource_data: K8sResourceData = None

    def refresh_resource_data(self) -> None:
        """Refresh resource data from the cluster."""
        api_instance = client.CoreV1Api()

        try:
            pods = api_instance.list_namespaced_pod(
                namespace=self.namespace, label_selector=self.label_selector
            )
        except ApiException:
            return None

        pod_data = []
        now = datetime.now(timezone.utc)
        for pod in pods.items:
            age_display = format_age(
                (now - pod.metadata.creation_timestamp).seconds
            )
            pod_data.append(
                {
                    "values": [
                        pod.metadata.name,
                        pod.status.phase,
                        pod.status.pod_ip or "-",
                        pod.metadata.namespace,
                        age_display,
                    ],
                    "style": "info",
                }
            )

        self.resource_data = K8sResourceData(
            name=self.name,
            namespace=self.namespace,
            col_meta=[
                {"name": "NAME", "width": None, "align": "left"},
                {"name": "STATUS", "width": 10, "align": "left"},
                {"name": "IP", "width": 15, "align": "left"},
                {"name": "NAMESPACE", "width": 15, "align": "left"},
                {"name": "AGE", "width": 10, "align": "left"},
            ],
            bindings=_Bindings(
                [
                    Binding(
                        "enter",
                        "select_row('Containers')",
                        "Show Containers",
                        show=True,
                    ),
                    Binding("d", "show_description", "Description", show=True),
                    Binding("ctrl+d", "delete_resource", "Delete", show=True),
                ]
            ),
            data=pod_data,
            selector={"label": "pod=", "index": 0},
        )

    def get_description(self, name: str) -> str:
        """Get the description of the specified pod."""
        api_instance = client.CoreV1Api()
        try:
            pod = api_instance.read_namespaced_pod(
                name=name, namespace=self.namespace
            )
            return yaml.dump(pod.to_dict(), default_flow_style=False)
        except ApiException:
            pass
        return ""

    def delete_resource(self, name: str) -> None:
        """Delete the specified pod."""
        api_instance = client.CoreV1Api()
        try:
            api_instance.delete_namespaced_pod(
                name=name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground", grace_period_seconds=5
                ),
            )
        except ApiException:
            pass

    def get_resource_data(self) -> K8sResourceData:
        """Return the current resource data."""
        if self.resource_data is None:
            self.refresh_resource_data()
        return self.resource_data
