from datetime import datetime, timezone
from kubernetes import client
from ttork.utilities import format_age
from ttork.models import K8sResourceData
from textual.binding import Binding, _Bindings


def get_pods(namespace: str, label_selector: str = None) -> K8sResourceData:
    """Get the Pod resources from the cluster."""
    api_instance = client.CoreV1Api()
    pods = api_instance.list_namespaced_pod(
        namespace=namespace, label_selector=label_selector
    )
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
    return K8sResourceData(
        name="Pods",
        namespace=namespace,
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
            ]
        ),
        data=pod_data,
    )
