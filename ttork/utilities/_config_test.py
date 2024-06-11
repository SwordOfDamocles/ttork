"""
This module is used to test the config module.
"""

from ._config import read_yaml_config, is_valid_config

import unittest
from unittest.mock import patch, mock_open


class TestYamlConfig(unittest.TestCase):

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=(
            "k8s:\n  context: test\n  namespace: default\nprojects:\n"
            "  - name: project1\n    tiltFilePath: /path/to/tiltfile"
        ),
    )
    def test_read_yaml_config_success(self, mock_file):
        file_path = "dummy_path.yaml"
        expected_output = {
            "k8s": {"context": "test", "namespace": "default"},
            "projects": [
                {"name": "project1", "tiltFilePath": "/path/to/tiltfile"}
            ],
        }
        result = read_yaml_config(file_path)
        self.assertEqual(result, expected_output)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_read_yaml_config_file_not_found(self, mock_file):
        file_path = "non_existent_file.yaml"
        result = read_yaml_config(file_path)
        self.assertEqual(result, {})

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="invalid_yaml: [unclosed_list",
    )
    def test_read_yaml_config_yaml_error(self, mock_file):
        file_path = "invalid_yaml.yaml"
        result = read_yaml_config(file_path)
        self.assertEqual(result, {})

    def test_is_valid_config_success(self):
        config_data = {
            "k8s": {"context": "test", "namespace": "default"},
            "projects": [
                {"name": "project1", "tiltFilePath": "/path/to/tiltfile"}
            ],
        }
        self.assertTrue(is_valid_config(config_data))

    def test_is_valid_config_missing_k8s(self):
        config_data = {
            "projects": [
                {"name": "project1", "tiltFilePath": "/path/to/tiltfile"}
            ]
        }
        self.assertFalse(is_valid_config(config_data))

    def test_is_valid_config_missing_context(self):
        config_data = {
            "k8s": {"namespace": "default"},
            "projects": [
                {"name": "project1", "tiltFilePath": "/path/to/tiltfile"}
            ],
        }
        self.assertFalse(is_valid_config(config_data))

    def test_is_valid_config_missing_namespace(self):
        config_data = {
            "k8s": {"context": "test"},
            "projects": [
                {"name": "project1", "tiltFilePath": "/path/to/tiltfile"}
            ],
        }
        self.assertFalse(is_valid_config(config_data))

    def test_is_valid_config_no_projects(self):
        config_data = {
            "k8s": {"context": "test", "namespace": "default"},
            "projects": [],
        }
        self.assertFalse(is_valid_config(config_data))

    def test_is_valid_config_missing_project_name(self):
        config_data = {
            "k8s": {"context": "test", "namespace": "default"},
            "projects": [{"tiltFilePath": "/path/to/tiltfile"}],
        }
        self.assertFalse(is_valid_config(config_data))

    def test_is_valid_config_missing_tiltfile_path(self):
        config_data = {
            "k8s": {"context": "test", "namespace": "default"},
            "projects": [{"name": "project1"}],
        }
        self.assertFalse(is_valid_config(config_data))


if __name__ == "__main__":
    unittest.main()
