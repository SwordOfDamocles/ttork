from datetime import datetime, timezone
from kubernetes import client
from ttork.utilities import format_age
from ttork.models import K8sResourceData
from textual.binding import Binding, _Bindings


def get_containers(
    namespace: str, label_selector: str = None
) -> K8sResourceData:
    """Get the Containers resources from the cluster."""
    # We only need the containers if the pod label_selector is not None
    if label_selector is None:
        return None
    else:
        pod_name = label_selector.split("=")[1]

    now = datetime.now(timezone.utc)
    api_instance = client.CoreV1Api()

    # Grab the pod information, which includes the container information
    pod = api_instance.read_namespaced_pod(name=pod_name, namespace=namespace)

    container_data = []

    # Check for regular containers
    if pod.status.container_statuses is None:
        container_status = []
    else:
        container_status = pod.status.container_statuses

    for container in container_status:
        age_display = format_age(
            (now - container.state.running.started_at).seconds
        )
        container_data.append(
            {
                "values": [
                    container.name,
                    container.image,
                    "TRUE" if container.ready else "FALSE",
                    get_container_state(container),
                    "standard",
                    str(container.restart_count),
                    age_display,
                ],
                "style": "info",
            }
        )

    # Check for init containers
    if pod.status.init_container_statuses is None:
        init_container_status = []
    else:
        init_container_status = pod.status.init_container_statuses

    for container in init_container_status:
        age_display = format_age(
            (now - container.state.running.started_at).seconds
        )
        container_data.append(
            {
                "values": [
                    container.name,
                    container.image,
                    "TRUE" if container.ready else "FALSE",
                    get_container_state(container),
                    "init",
                    str(container.restart_count),
                    age_display,
                ],
                "style": "info",
            }
        )

    # Check for ephemeral containers
    if pod.status.ephemeral_container_statuses is None:
        eph_container_status = []
    else:
        eph_container_status = pod.status.ephemeral_container_statuses

    for container in eph_container_status:
        age_display = format_age(
            (now - container.state.running.started_at).seconds
        )
        container_data.append(
            {
                "values": [
                    container.name,
                    container.image,
                    "TRUE" if container.ready else "FALSE",
                    get_container_state(container),
                    "ephemeral",
                    str(container.restart_count),
                    age_display,
                ],
                "style": "info",
            }
        )

    return K8sResourceData(
        name="Containers",
        namespace=namespace,
        col_meta=[
            {"name": "NAME", "width": None, "align": "left"},
            {"name": "IMAGE", "width": None, "align": "left"},
            {"name": "READY", "width": 5, "align": "left"},
            {"name": "STATE", "width": 15, "align": "left"},
            {"name": "TYPE", "width": 10, "align": "left"},
            {"name": "RESTARTS", "width": 8, "align": "left"},
            {"name": "AGE", "width": 10, "align": "left"},
        ],
        bindings=_Bindings(
            [
                Binding(
                    "enter",
                    "select_row('Logs')",
                    "Show Containers",
                    show=True,
                ),
            ]
        ),
        data=container_data,
    )


def get_container_state(container_status):
    """Get the state of the container."""
    if container_status.state.waiting is not None:
        if container_status.state.waiting.reason is not None:
            return container_status.state.waiting.reason
        return "Waiting"
    elif container_status.state.terminated is not None:
        if container_status.state.terminated.reason is not None:
            return container_status.state.terminated.reason
        return "Terminating"
    elif container_status.state.running is not None:
        return "Running"
    else:
        return "Unknown"
