import requests


def get_tilt_status(port: int) -> dict:
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
