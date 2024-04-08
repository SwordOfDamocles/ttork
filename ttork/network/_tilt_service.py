import copy
import os
import socket
import subprocess
import requests
import atexit
from signal import SIGKILL


class TiltService:
    """Runs and tracks status on Tilt services."""

    def __init__(self, app_config, logger):
        self.status_info = {}
        self.log = logger
        atexit.register(self.cleanup)
        self.processes = []

        for project in app_config.get("projects", []):
            if "tiltFilePath" in project:
                self.status_info[project["tiltFilePath"]] = dict(
                    name=project.get("name", "NameUnset"),
                    uiResources=[],
                    service_online=False,
                    port=0,
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

    def start_tilt_processes(self) -> None:
        next_free_port = get_next_free_port(10350)
        for pkey in self.status_info:
            if os.path.exists(pkey):
                if self.status_info[pkey]["port"] == 0:
                    # Grab the next free port, starting at 10350
                    next_free_port = get_next_free_port(next_free_port)
                    self.status_info[pkey]["port"] = next_free_port
                    next_free_port += 1

                tilt_startup_command = [
                    "tilt",
                    "up",
                    f"--port={self.status_info[pkey]['port']}",
                    f"--file={pkey}",
                ]

                self.log.debug(f"Starting Tilt process: {tilt_startup_command}")
                self.log.debug(
                    f"Starting Tilt process in: {os.path.dirname(pkey)}"
                )
                process = subprocess.Popen(
                    " ".join(tilt_startup_command),
                    shell=True,
                    cwd=os.path.dirname(pkey),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                self.log.debug(f"Started process: {process.pid}")
                self.processes.append(process)

    def stop_tilt_processes(self) -> None:
        # Terminate all running processes
        for process in self.processes:
            print(f"Terminating process: {process.pid}")
            os.kill(process.pid, SIGKILL)

        # Tilt resource cleanup
        # for pkey in self.status_info:
        #     if self.status_info[pkey]["port"] > 0:
        #         os.kill(get_process_id(self.status_info[pkey]["port"]), 9)
        #     tilt_shutdown_command = f"tilt down --file={pkey}"
        #     subprocess.run(tilt_shutdown_command, shell=True)

        self.processes.clear()

    def cleanup(self) -> None:
        self.stop_tilt_processes()
        self.status_info.clear()

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def __del__(self):
        self.cleanup()


def get_next_free_port(start_port: int) -> int:
    """Get the next free port starting at start_port.

    Args:
        start_port (int): The port to start checking from.

    Returns:
        int: The next free port.
    """
    port = start_port
    while not is_port_free(port):
        port += 1
    return port


def is_port_free(port: int) -> bool:
    """Check if a port is free.

    Args:
        port (int): The port to check.

    Returns:
        bool: True if the port is free, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) != 0
