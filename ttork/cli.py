from .app import TTorkApp
from ttork.utilities import read_yaml_config, is_valid_config


def main():
    # Pull in the configuration data
    ttork_conf = read_yaml_config("./ttork.yaml")
    if not is_valid_config(ttork_conf):
        return

    # Start the application
    app = TTorkApp()
    app.ttork_config = ttork_conf
    app.run()


if __name__ == "__main__":
    main()
