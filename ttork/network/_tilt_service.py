import copy
import os
import socket
import subprocess
import requests
import atexit
import logging
from signal import SIGKILL


class TiltService:
    """Runs and tracks status on Tilt services."""

    def __init__(self, app_config: dict, logger: logging.Logger) -> None:
        self.status_info = {}
        self.log = logger
        atexit.register(self.cleanup)
        self.processes = []

        for project in app_config.get("projects", []):
            env_vars = {}
            for env_var in project.get("environment", []):
                env_vars[env_var["name"]] = env_var["value"]
            if "tiltFilePath" in project:
                self.status_info[project["tiltFilePath"]] = dict(
                    name=project.get("name", "NameUnset"),
                    uiResources=[],
                    env_vars=env_vars,
                    service_online=False,
                    port=0,
                    pid=0,
                )

    def update_status_info(self) -> None:
        """Refresh the status_info struct with information about
        the running Tilt instances.
        """
        for pkey in self.status_info:
            port = self.status_info[pkey]["port"]
            if port > 0:
                status_json = self.get_tilt_status(port)
                if status_json:
                    self.status_info[pkey]["uiResources"] = status_json.get(
                        "uiResources", []
                    )
                    self.status_info[pkey]["service_online"] = True
                else:
                    self.status_info[pkey]["uiResources"].clear()
                    self.status_info[pkey]["service_online"] = False

    def get_tilt_status(self, port: int) -> dict:
        """Get the Tilt Status from the running tilt instance, specified
        by port.

        Returns:
            dict: json response dictionary, or None
        """
        tilt_url = f"http://localhost:{port}/api/view"

        try:
            response = requests.get(tilt_url)

            # Check the response status code
            if response.status_code == 200:
                # The request was successful
                json_response = response.json()
            else:
                # The request failed
                print(
                    "Error querying tilt status: {}".format(
                        response.status_code,
                    )
                )
                return None

            return json_response
        except Exception:
            return None

    def get_status_info(self) -> dict:
        """Get a copy of the current status info struct, to be used
        to check for changes to the status.

        Returns:
            dict: copy.deepcopy of the status_info dictionary
        """
        return copy.deepcopy(self.status_info)

    def start_tilt_process(self, project_key: str) -> None:
        """Start up a single Tilt process, by project key."""
        if project_key in self.status_info:
            if (
                os.path.exists(project_key)
                and self.status_info[project_key]["service_online"] is False
            ):
                if self.status_info[project_key]["port"] == 0:
                    next_free_port = self.get_free_port()
                    if next_free_port < 0:
                        self.log.error(
                            "No free ports available, "
                            "unable to start Tilt process."
                        )
                        return
                    self.status_info[project_key]["port"] = next_free_port

                tilt_startup_command = [
                    "tilt",
                    "up",
                    f"--port={self.status_info[project_key]['port']}",
                    f"--file={project_key}",
                ]

                self.log.debug(
                    f"Tilt process startup command: {tilt_startup_command}"
                )
                self.log.debug(
                    f"Starting Tilt process in: {os.path.dirname(project_key)}"
                )
                tilt_env = os.environ.copy()
                for env_var in self.status_info[project_key]["env_vars"]:
                    tilt_env[env_var] = self.status_info[project_key][
                        "env_vars"
                    ][env_var]
                process = subprocess.Popen(
                    " ".join(tilt_startup_command),
                    shell=True,
                    cwd=os.path.dirname(project_key),
                    env=tilt_env,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                self.log.debug(f"Started process: {process.pid}")
                self.status_info[project_key]["pid"] = process.pid
                self.processes.append(process)

    def start_tilt_processes(self) -> None:
        """Bring up all Tilt projects."""
        for pkey in self.status_info:
            self.start_tilt_process(pkey)

    def tear_down_all_resources(self) -> None:
        """Tear down all Tilt projects."""
        for project_key in self.status_info:
            self.tear_down_tilt_resources(project_key)

    def tear_down_tilt_resources(self, project_key: str) -> None:
        """Tear down Tilt resources of a single project, by project key."""
        if project_key in self.status_info:

            # First, make sure the Tilt process isn't running
            self.stop_tilt_process(project_key)

            # Then do 'tilt down' command to clean up any tilt-generated
            # resources
            tilt_down_command = [
                "tilt",
                "down",
                f"--file={project_key}",
            ]

            self.log.debug(f"Tearing down Tilt Resources: {project_key}")

            subprocess.Popen(
                " ".join(tilt_down_command),
                shell=True,
                cwd=os.path.dirname(project_key),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

    def stop_tilt_process(self, project_key: str) -> None:
        """Kill single running Tilt process, by project key.

        Terminate the running Tilt process, and clear the pid from the
        status_info struct.
        """
        if (
            project_key in self.status_info
            and self.status_info[project_key]["pid"] > 0
        ):
            self.log.debug(
                f"Terminating process: {project_key}:"
                f"{self.status_info[project_key]['pid']}"
            )
            os.kill(self.status_info[project_key]["pid"], SIGKILL)
            self.status_info[project_key]["pid"] = 0
            self.status_info[project_key]["service_online"] = False

    def stop_tilt_processes(self) -> None:
        """Kill all running Tilt processes."""
        for pkey in self.status_info:
            self.stop_tilt_process(pkey)

        # Clear out the processes list
        self.processes.clear()

    def get_free_port(self) -> int:
        """Get the next free port starting at 10350.

        Returns:
            int: The next free port.
        """
        start_port = 10350

        # Check status_info for any ports in use
        used_ports = [pinfo["port"] for pinfo in self.status_info.values()]

        while start_port in used_ports or not is_port_free(start_port):
            start_port += 1

        if start_port < 65535:
            return start_port
        else:
            return -1

    def cleanup(self) -> None:
        self.stop_tilt_processes()
        self.status_info.clear()

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def __del__(self):
        self.cleanup()


def is_port_free(port: int) -> bool:
    """Check if a port is free.

    Args:
        port (int): The port to check.

    Returns:
        bool: True if the port is free, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0
