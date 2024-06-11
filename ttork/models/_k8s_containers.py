from os import system
from datetime import datetime, timezone
from kubernetes import client
from kubernetes.client.rest import ApiException
from textual.binding import Binding, _Bindings
from textual.app import App

from ttork.utilities import format_age
from ttork.models import K8sResourceData


class K8sContainers:
    """K8sContainers is a model for Kubernetes Containers."""

    def __init__(self, namespace: str) -> None:
        self.name: str = "Containers"
        self.namespace: str = namespace
        self.label_selector: str = None
        self.resource_data: K8sResourceData = None
        self.pod_name: str = None

    def refresh_resource_data(self) -> None:
        """Get the Containers resources from the cluster."""
        # We only need the containers if the pod label_selector is not None
        if self.label_selector is None:
            return None
        else:
            pod_name = self.label_selector.split("=")[1]
            self.pod_name = pod_name

        now = datetime.now(timezone.utc)
        api_instance = client.CoreV1Api()

        # Grab the pod information, which includes the container information
        try:
            pod = api_instance.read_namespaced_pod(
                name=pod_name, namespace=self.namespace
            )
        except ApiException:
            return None

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
                        self.get_container_state(container),
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
                        self.get_container_state(container),
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
                        self.get_container_state(container),
                        "ephemeral",
                        str(container.restart_count),
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
                        "Show Logs",
                        show=True,
                    ),
                    Binding(
                        "s",
                        "resource_call('open_shell')",
                        "Open Shell",
                        show=True,
                    ),
                ]
            ),
            data=container_data,
        )

    def get_resource_data(self) -> K8sResourceData:
        if self.resource_data is None:
            self.refresh_resource_data()
        return self.resource_data

    def get_container_state(self, container_status):
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

    def get_container_logs(self, container_name: str, pod_name: str):
        """Get the logs for the specified container."""
        api_instance = client.CoreV1Api()
        try:
            logs = api_instance.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                container=container_name,
                tail_lines=100,
            )
            return logs
        except ApiException:
            pass
        return ""

    def open_shell(self, app: App, row: list):
        """Open a shell in the specified container."""
        container_name = str(row[0])
        command = (
            "clear;kubectl exec -it {0} --container {1} -- /bin/sh".format(
                self.pod_name, container_name
            )
        )
        with app.suspend():
            system(command)
