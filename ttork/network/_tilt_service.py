import copy
import requests


class TiltService:
    """Runs and tracks status on Tilt services."""

    def __init__(self, app_config):
        self.status_info = {}
        for project in app_config.get("projects", []):
            if "tiltFilePath" in project:
                self.status_info[project["tiltFilePath"]] = dict(
                    name=project.get("name", "NameUnset"),
                    uiResources=[],
                    service_online=False,
                    port=0,
                )

        # TODO: Remove: For Development Only
        self.status_info[
            "/Users/awaller/waller_dev/projects/rcwl/seeder/Tiltfile"
        ]["port"] = 10350

    def update_status_info(self) -> None:
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
        return copy.deepcopy(self.status_info)
