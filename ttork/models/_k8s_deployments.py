import yaml
from datetime import datetime, timezone
from kubernetes import client
from kubernetes.client.rest import ApiException
from textual.binding import Binding, _Bindings


from ttork.utilities import format_age
from ttork.models import K8sResourceData


class K8sDeployments:
    """K8sDeployments is a model for Kubernetes Deployments."""

    def __init__(self, namespace: str) -> None:
        self.name: str = "Deployments"
        self.namespace: str = namespace
        self.label_selector: str = None
        self.resource_data: K8sResourceData = None

    def refresh_resource_data(self) -> None:
        """Refresh resource data from the cluster."""
        api_instance = client.AppsV1Api()

        try:
            deployments = api_instance.list_namespaced_deployment(
                namespace=self.namespace, label_selector=self.label_selector
            )
        except ApiException:
            return None

        deployment_data = []
        now = datetime.now(timezone.utc)
        for deployment in deployments.items:
            age_display = format_age(
                (now - deployment.metadata.creation_timestamp).seconds
            )
            deployment_data.append(
                {
                    "values": [
                        deployment.metadata.name,
                        "{0}/{1}".format(
                            deployment.status.ready_replicas or 0,
                            deployment.status.replicas,
                        ),
                        str(deployment.status.replicas),
                        str(deployment.status.available_replicas),
                        deployment.metadata.namespace,
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
                {"name": "READY", "width": 10, "align": "left"},
                {"name": "CURRENT", "width": 7, "align": "center"},
                {"name": "AVAILABLE", "width": 9, "align": "center"},
                {"name": "NAMESPACE", "width": 20, "align": "left"},
                {"name": "AGE", "width": 10, "align": "left"},
            ],
            bindings=_Bindings(
                [
                    Binding(
                        "enter", "select_row('Pods')", "Show Pods", show=True
                    ),
                    Binding("d", "show_description", "Description", show=True),
                    Binding("ctrl+d", "delete_resource", "Delete", show=True),
                ]
            ),
            data=deployment_data,
            selector={"label": "app=", "index": 0},
        )

    def get_description(self, name: str) -> str:
        """Get the description of the specified Deployment."""
        api_instance = client.AppsV1Api()
        try:
            deployment = api_instance.read_namespaced_deployment(
                name=name, namespace=self.namespace
            )
            return yaml.dump(deployment.to_dict(), default_flow_style=False)
        except ApiException:
            pass
        return ""

    def delete_resource(self, name: str) -> None:
        """Delete the specified Deployment."""
        api_instance = client.AppsV1Api()
        api_instance.delete_namespaced_deployment(
            name=name,
            namespace=self.namespace,
            body=client.V1DeleteOptions(
                propagation_policy="Foreground", grace_period_seconds=5
            ),
        )

    def get_resource_data(self) -> K8sResourceData:
        """Return the current resource data."""
        if self.resource_data is None:
            self.refresh_resource_data()
        return self.resource_data
