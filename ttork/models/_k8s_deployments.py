from datetime import datetime, timezone
from kubernetes import client
from ttork.utilities import format_age
from ttork.models import K8sResourceData


def get_deployments(namespace: str) -> K8sResourceData:
    """Get the Deployment resources from the cluster."""
    api_instance = client.AppsV1Api()
    deployments = api_instance.list_namespaced_deployment(namespace=namespace)
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
    return K8sResourceData(
        name="Deployments",
        namespace=namespace,
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
