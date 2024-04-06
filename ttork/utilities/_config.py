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
