from .app import TTorkApp
from ttork.utilities import read_yaml_config


def main():
    ttork_conf = read_yaml_config("./ttork.yaml")
    app = TTorkApp()
    app.ttork_config = ttork_conf
    app.run()


if __name__ == "__main__":
    main()
