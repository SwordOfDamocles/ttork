import yaml


def read_yaml_config(file_path):
    """
    Read YAML configuration file and return its values as a dictionary.

    Parameters:
        file_path (str): Path to the YAML configuration file.

    Returns:
        dict: Dictionary containing the configuration values.
    """
    try:
        with open(file_path, "r") as file:
            config_data = yaml.safe_load(file)
        return config_data
    except FileNotFoundError:
        print(f"Error: Config file '{file_path}' not found.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        return {}


def is_valid_config(config_data):
    """
    Validate the configuration data.

    Parameters:
        config_data (dict): Dictionary containing the configuration values.

    Returns:
        bool: True if the configuration is valid, False otherwise.
    """
    if "k8s" not in config_data:
        print("Error: 'k8s' section missing from config file.")
        return False
    if "context" not in config_data["k8s"]:
        print("Error: 'context' missing from 'k8s' section.")
        return False
    if "namespace" not in config_data["k8s"]:
        print("Error: 'namespace' missing from 'k8s' section.")
        return False
    if len(config_data["projects"]) == 0:
        print("Error: No projects defined in 'projects' section.")
        return False
    for project in config_data["projects"]:
        if "name" not in project:
            print("Error: 'name' missing from project definition.")
            return False
        if "tiltFilePath" not in project:
            print("Error: 'tiltFilePath' missing from project definition.")
            return False
    return True
