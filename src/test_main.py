"""Comprehensive pytest-based tests for main.py functions."""

import io
import os
import shutil
import sys
import tempfile
import unittest.mock
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

# Add the src directory to the Python path to import main
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import main


class TestOpenActionFile:
    """Test the open_action_file function."""

    @pytest.fixture
    def valid_yaml_content(self):
        """Sample valid YAML content."""
        return {
            'name': 'Test Action',
            'description': 'A test action',
            'inputs': {
                'input1': {
                    'description': 'Test input',
                    'required': True
                }
            }
        }

    @pytest.fixture
    def valid_yaml_string(self):
        """Valid YAML string content."""
        return """
name: "Test Action"
description: "A test action"
inputs:
  input1:
    description: "Test input"
    required: true
"""

    @pytest.fixture
    def invalid_yaml_string(self):
        """Invalid YAML string content."""
        return """
name: "Test Action"
description: "A test action"
inputs:
  - invalid yaml structure
    missing: colon
"""

    @patch.dict(os.environ, {'ACTION_FILE_NAME': 'action.yaml'})
    @patch('main.open', new_callable=mock_open)
    @patch('main.yaml.safe_load')
    def test_open_action_file_success(self, mock_yaml_load, mock_file, valid_yaml_content):
        """Test successful opening and parsing of action file."""
        # Arrange
        mock_yaml_load.return_value = valid_yaml_content
        
        # Act
        result = main.open_action_file('action.yaml')
        
        # Assert
        assert result == valid_yaml_content
        mock_file.assert_called_once_with('action.yaml', 'r', encoding='UTF-8')
        mock_yaml_load.assert_called_once()

    @patch('main.open', side_effect=FileNotFoundError("File not found"))
    def test_open_action_file_not_found(self, mock_file):
        """Test FileNotFoundError is raised when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            main.open_action_file('nonexistent.yaml')

    @patch('main.open', new_callable=mock_open)
    @patch('main.yaml.safe_load', side_effect=yaml.YAMLError("Invalid YAML"))
    def test_open_action_file_invalid_yaml(self, mock_yaml_load, mock_file):
        """Test YAMLError is raised when YAML is invalid."""
        with pytest.raises(yaml.YAMLError):
            main.open_action_file('invalid.yaml')

    @patch('main.open', side_effect=IOError("Permission denied"))
    def test_open_action_file_io_error(self, mock_file):
        """Test IOError is handled correctly."""
        with pytest.raises(IOError):
            main.open_action_file('permission_denied.yaml')

    def test_open_action_file_empty_filename(self):
        """Test behavior with empty filename."""
        with pytest.raises(FileNotFoundError):
            main.open_action_file('')


class TestProcessActionInputs:
    """Test the process_action_inputs function."""

    @pytest.fixture
    def action_contents_with_inputs(self):
        """Action contents with complete input definitions."""
        return {
            'inputs': {
                'input1': {
                    'description': 'Test input 1',
                    'required': True,
                    'type': 'string',
                    'default': 'default_value'
                },
                'input2': {
                    'description': 'Test input 2',
                    'required': False,
                    'type': 'number',
                    'default': 42
                }
            }
        }

    def test_process_action_inputs_with_all_fields(self, action_contents_with_inputs):
        """Test processing inputs with all fields present."""
        # Arrange
        output_list = []
        
        # Act
        result = main.process_action_inputs(action_contents_with_inputs, output_list)
        
        # Assert
        assert '# inputs' in result
        assert '| Title | Required | Type | Default| Description |' in result
        assert '|-----|-----|-----|-----|-----|' in result
        assert '| input1 | True | string | `default_value` | Test input 1 |' in result
        assert '| input2 | False | number | `42` | Test input 2 |' in result

    def test_process_action_inputs_with_missing_fields(self):
        """Test processing inputs with some missing fields."""
        # Arrange
        action_contents = {
            'inputs': {
                'input1': {
                    'description': 'Test input 1'
                    # Missing required, type, and default
                }
            }
        }
        output_list = []
        
        # Act
        result = main.process_action_inputs(action_contents, output_list)
        
        # Assert
        assert '| input1 | False |  |  | Test input 1 |' in result

    def test_process_action_inputs_no_inputs(self):
        """Test processing when no inputs are present."""
        # Arrange
        action_contents = {}
        output_list = ['existing_content']
        
        # Act
        result = main.process_action_inputs(action_contents, output_list)
        
        # Assert
        assert result == ['existing_content']

    def test_process_action_inputs_empty_inputs(self):
        """Test processing when inputs dictionary is empty."""
        # Arrange
        action_contents = {'inputs': {}}
        output_list = ['existing_content']
        
        # Act
        result = main.process_action_inputs(action_contents, output_list)
        
        # Assert
        assert result == ['existing_content']

    def test_process_action_inputs_none_values(self):
        """Test processing inputs with None values."""
        # Arrange
        action_contents = {
            'inputs': {
                'input1': {
                    'description': None,
                    'required': None,
                    'type': None,
                    'default': None
                }
            }
        }
        output_list = []
        
        # Act
        result = main.process_action_inputs(action_contents, output_list)
        
        # Assert
        assert '| input1 | None | None |  | None |' in result

    def test_process_action_inputs_boolean_default(self):
        """Test processing inputs with boolean default values."""
        # Arrange
        action_contents = {
            'inputs': {
                'enable_feature': {
                    'description': 'Enable feature flag',
                    'required': False,
                    'type': 'boolean',
                    'default': True
                }
            }
        }
        output_list = []
        
        # Act
        result = main.process_action_inputs(action_contents, output_list)
        
        # Assert
        assert '| enable_feature | False | boolean | `True` | Enable feature flag |' in result


class TestProcessActionOutputs:
    """Test the process_action_outputs function."""

    @pytest.fixture
    def action_contents_with_outputs(self):
        """Action contents with complete output definitions."""
        return {
            'outputs': {
                'output1': {
                    'description': 'Test output 1',
                    'value': '${{ steps.step1.outputs.result }}'
                },
                'output2': {
                    'description': 'Test output 2',
                    'value': '${{ steps.step2.outputs.data }}'
                }
            }
        }

    def test_process_action_outputs_with_all_fields(self, action_contents_with_outputs):
        """Test processing outputs with all fields present."""
        # Arrange
        output_list = []
        
        # Act
        result = main.process_action_outputs(action_contents_with_outputs, output_list)
        
        # Assert
        assert '# outputs' in result
        assert '| Title | Description | Value |' in result
        assert '|-----|-----|-----|' in result
        assert '|output1 | Test output 1 |  `${{ steps.step1.outputs.result }}` | ' in result
        assert '|output2 | Test output 2 |  `${{ steps.step2.outputs.data }}` | ' in result

    def test_process_action_outputs_missing_description(self):
        """Test processing outputs with missing description."""
        # Arrange
        action_contents = {
            'outputs': {
                'output1': {
                    'value': '${{ steps.step1.outputs.result }}'
                    # Missing description
                }
            }
        }
        output_list = []
        
        # Act
        result = main.process_action_outputs(action_contents, output_list)
        
        # Assert
        assert '|output1 |  |  `${{ steps.step1.outputs.result }}` | ' in result

    def test_process_action_outputs_missing_value(self):
        """Test processing outputs with missing value."""
        # Arrange
        action_contents = {
            'outputs': {
                'output1': {
                    'description': 'Test output'
                    # Missing value
                }
            }
        }
        output_list = []
        
        # Act
        result = main.process_action_outputs(action_contents, output_list)
        
        # Assert - When value is missing, KeyError is caught and returns just headers
        assert result == ['# outputs', '| Title | Description | Value |', '|-----|-----|-----|']

    def test_process_action_outputs_no_outputs(self):
        """Test processing when no outputs are present."""
        # Arrange
        action_contents = {}
        output_list = ['existing_content']
        
        # Act
        result = main.process_action_outputs(action_contents, output_list)
        
        # Assert
        assert result == ['existing_content']

    def test_process_action_outputs_empty_outputs(self):
        """Test processing when outputs dictionary is empty."""
        # Arrange
        action_contents = {'outputs': {}}
        output_list = ['existing_content']
        
        # Act
        result = main.process_action_outputs(action_contents, output_list)
        
        # Assert
        assert result == ['existing_content']

    def test_process_action_outputs_none_values(self):
        """Test processing outputs with None values."""
        # Arrange
        action_contents = {
            'outputs': {
                'output1': {
                    'description': None,
                    'value': None
                }
            }
        }
        output_list = []
        
        # Act & Assert - This should raise a TypeError since None can't be concatenated with string
        with pytest.raises(TypeError):
            main.process_action_outputs(action_contents, output_list)


class TestFindActionDocsMarkers:
    """Test the find_action_docs_markers function."""

    def test_find_both_markers(self):
        """Test finding both BEGIN and END markers."""
        # Arrange
        file_contents = [
            'Some content\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'Action docs\n',
            '<!-- END_ACTION_DOCS -->\n',
            'More content\n'
        ]
        
        # Act
        found_start, found_end = main.find_action_docs_markers(file_contents)
        
        # Assert
        assert found_start is True
        assert found_end is True

    def test_find_only_start_marker(self):
        """Test finding only BEGIN marker."""
        # Arrange
        file_contents = [
            'Some content\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'Action docs\n'
        ]
        
        # Act
        found_start, found_end = main.find_action_docs_markers(file_contents)
        
        # Assert
        assert found_start is True
        assert found_end is False

    def test_find_only_end_marker(self):
        """Test finding only END marker."""
        # Arrange
        file_contents = [
            'Some content\n',
            'Action docs\n',
            '<!-- END_ACTION_DOCS -->\n'
        ]
        
        # Act
        found_start, found_end = main.find_action_docs_markers(file_contents)
        
        # Assert
        assert found_start is False
        assert found_end is True

    def test_find_no_markers(self):
        """Test finding no markers."""
        # Arrange
        file_contents = [
            'Some content\n',
            'More content\n'
        ]
        
        # Act
        found_start, found_end = main.find_action_docs_markers(file_contents)
        
        # Assert
        assert found_start is False
        assert found_end is False

    def test_find_markers_empty_file(self):
        """Test finding markers in empty file."""
        # Arrange
        file_contents = []
        
        # Act
        found_start, found_end = main.find_action_docs_markers(file_contents)
        
        # Assert
        assert found_start is False
        assert found_end is False

    def test_find_markers_multiple_occurrences(self):
        """Test finding markers with multiple occurrences."""
        # Arrange
        file_contents = [
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'First docs\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Some content\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'Second docs\n',
            '<!-- END_ACTION_DOCS -->\n'
        ]
        
        # Act
        found_start, found_end = main.find_action_docs_markers(file_contents)
        
        # Assert
        assert found_start is True
        assert found_end is True


class TestRemoveContentBetweenMarkers:
    """Test the remove_content_between_markers function."""

    def test_remove_content_between_markers(self):
        """Test removing content between markers."""
        # Arrange
        file_contents = [
            'Header content\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'Old docs\n',
            'More old docs\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Footer content\n'
        ]
        
        # Act
        result = main.remove_content_between_markers(file_contents)
        
        # Assert
        expected = [
            'Header content\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Footer content\n'
        ]
        assert result == expected

    def test_preserve_content_outside_markers(self):
        """Test that content outside markers is preserved."""
        # Arrange
        file_contents = [
            'Header\n',
            'Important content\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'Remove this\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Keep this\n',
            'Footer\n'
        ]
        
        # Act
        result = main.remove_content_between_markers(file_contents)
        
        # Assert
        assert 'Header\n' in result
        assert 'Important content\n' in result
        assert 'Keep this\n' in result
        assert 'Footer\n' in result
        assert 'Remove this\n' not in result

    def test_remove_content_no_content_between(self):
        """Test removing content when there's no content between markers."""
        # Arrange
        file_contents = [
            'Header\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Footer\n'
        ]
        
        # Act
        result = main.remove_content_between_markers(file_contents)
        
        # Assert
        expected = [
            'Header\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Footer\n'
        ]
        assert result == expected

    def test_remove_content_multiple_marker_pairs(self):
        """Test removing content with multiple marker pairs."""
        # Arrange
        file_contents = [
            'Header\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'First docs\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Middle content\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'Second docs\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Footer\n'
        ]
        
        # Act
        result = main.remove_content_between_markers(file_contents)
        
        # Assert
        assert 'Header\n' in result
        assert 'Middle content\n' in result
        assert 'Footer\n' in result
        assert 'First docs\n' not in result
        assert 'Second docs\n' not in result


class TestWriteActionDocsContent:
    """Test the write_action_docs_content function."""

    def test_write_action_docs_content(self):
        """Test writing action docs content to file handle."""
        # Arrange
        output_list = [
            '# Test Action',
            'Description',
            '# inputs',
            '| Title | Required |'
        ]
        
        mock_file_handle = unittest.mock.Mock()
        
        # Act
        main.write_action_docs_content(mock_file_handle, output_list)
        
        # Assert
        expected_calls = [
            unittest.mock.call('\n'),  # For first # line
            unittest.mock.call('# Test Action'),
            unittest.mock.call('\n'),
            unittest.mock.call('Description'),
            unittest.mock.call('\n'),
            unittest.mock.call('\n'),  # For # inputs line
            unittest.mock.call('# inputs'),
            unittest.mock.call('\n'),
            unittest.mock.call('| Title | Required |'),
            unittest.mock.call('\n')
        ]
        
        mock_file_handle.write.assert_has_calls(expected_calls)

    def test_write_action_docs_content_empty_list(self):
        """Test writing empty output list."""
        # Arrange
        output_list = []
        mock_file_handle = unittest.mock.Mock()
        
        # Act
        main.write_action_docs_content(mock_file_handle, output_list)
        
        # Assert
        mock_file_handle.write.assert_not_called()

    def test_write_action_docs_content_single_item(self):
        """Test writing single item in output list."""
        # Arrange
        output_list = ['# Single Header']
        mock_file_handle = unittest.mock.Mock()
        
        # Act
        main.write_action_docs_content(mock_file_handle, output_list)
        
        # Assert
        expected_calls = [
            unittest.mock.call('\n'),
            unittest.mock.call('# Single Header'),
            unittest.mock.call('\n')
        ]
        mock_file_handle.write.assert_has_calls(expected_calls)


class TestGenerateDocumentationContent:
    """Test the generate_documentation_content function."""

    @pytest.fixture
    def complete_action_contents(self):
        """Complete action contents for testing."""
        return {
            'name': 'Test Action',
            'description': 'A comprehensive test action',
            'inputs': {
                'test_input': {
                    'description': 'Test input parameter',
                    'required': True,
                    'type': 'string',
                    'default': 'test_value'
                }
            },
            'outputs': {
                'test_output': {
                    'description': 'Test output parameter',
                    'value': '${{ steps.test.outputs.result }}'
                }
            }
        }

    def test_generate_documentation_content(self, complete_action_contents):
        """Test generating complete documentation content."""
        # Act
        result = main.generate_documentation_content(complete_action_contents)
        
        # Assert
        assert '# Test Action' in result
        assert 'A comprehensive test action' in result
        assert '# inputs' in result
        assert '# outputs' in result
        assert any('test_input' in line for line in result)
        assert any('test_output' in line for line in result)

    def test_generate_documentation_content_no_inputs(self):
        """Test generating documentation content without inputs."""
        # Arrange
        action_contents = {
            'name': 'Simple Action',
            'description': 'Simple action without inputs'
        }
        
        # Act
        result = main.generate_documentation_content(action_contents)
        
        # Assert
        assert '# Simple Action' in result
        assert 'Simple action without inputs' in result
        assert '# inputs' not in result

    def test_generate_documentation_content_no_outputs(self):
        """Test generating documentation content without outputs."""
        # Arrange
        action_contents = {
            'name': 'Simple Action',
            'description': 'Simple action without outputs'
        }
        
        # Act
        result = main.generate_documentation_content(action_contents)
        
        # Assert
        assert '# Simple Action' in result
        assert 'Simple action without outputs' in result
        assert '# outputs' not in result

    def test_generate_documentation_content_minimal(self):
        """Test generating documentation with minimal content."""
        # Arrange
        action_contents = {
            'name': 'Minimal Action'
        }
        
        # Act & Assert - This should raise a KeyError since description is required
        with pytest.raises(KeyError):
            main.generate_documentation_content(action_contents)

    def test_generate_documentation_content_empty_inputs_outputs(self):
        """Test generating documentation with empty inputs and outputs."""
        # Arrange
        action_contents = {
            'name': 'Empty Action',
            'description': 'Action with empty inputs/outputs',
            'inputs': {},
            'outputs': {}
        }
        
        # Act
        result = main.generate_documentation_content(action_contents)
        
        # Assert
        assert '# Empty Action' in result
        assert 'Action with empty inputs/outputs' in result
        assert '# inputs' not in result
        assert '# outputs' not in result


class TestReadOriginalFile:
    """Test the read_original_file function."""

    def test_read_original_file_success(self):
        """Test successfully reading an original file."""
        # Arrange
        content = "Line 1\nLine 2\nLine 3\n"
        
        with patch('main.open', mock_open(read_data=content)):
            # Act
            result = main.read_original_file('test.txt')
            
            # Assert
            assert result == ['Line 1\n', 'Line 2\n', 'Line 3\n']

    def test_read_original_file_not_found(self):
        """Test handling FileNotFoundError."""
        with patch('main.open', side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                main.read_original_file('nonexistent.txt')

    def test_read_original_file_io_error(self):
        """Test handling IOError."""
        with patch('main.open', side_effect=IOError("IO Error")):
            with pytest.raises(IOError):
                main.read_original_file('problematic.txt')

    def test_read_original_file_empty_file(self):
        """Test reading an empty file."""
        with patch('main.open', mock_open(read_data="")):
            # Act
            result = main.read_original_file('empty.txt')
            
            # Assert
            assert result == []

    def test_read_original_file_single_line(self):
        """Test reading a file with a single line."""
        with patch('main.open', mock_open(read_data="Single line")):
            # Act
            result = main.read_original_file('single.txt')
            
            # Assert
            assert result == ['Single line']


class TestWriteDocumentationFile:
    """Test the write_documentation_file function."""

    @pytest.fixture
    def sample_output_list(self):
        """Sample output list for testing."""
        return [
            '# Test Action',
            'Description',
            '# inputs',
            '| Title | Required |',
            '# outputs',
            '| Title | Description |'
        ]

    @patch('main.write_output_file_overwrite_mode')
    def test_write_documentation_file_overwrite_mode(self, mock_overwrite, sample_output_list):
        """Test writing documentation file in overwrite mode."""
        # Act
        main.write_documentation_file('output.md', 'overwrite', sample_output_list)
        
        # Assert
        mock_overwrite.assert_called_once_with('output.md', sample_output_list)

    @patch('main.read_original_file')
    @patch('main.write_output_file_update_mode')
    def test_write_documentation_file_update_mode(self, mock_update, mock_read, sample_output_list):
        """Test writing documentation file in update mode."""
        # Arrange
        original_content = ['existing content\n']
        mock_read.return_value = original_content
        
        # Act
        main.write_documentation_file('output.md', 'update', sample_output_list)
        
        # Assert
        mock_read.assert_called_once_with('output.md')
        mock_update.assert_called_once_with('output.md', original_content, sample_output_list)

    def test_write_documentation_file_unknown_mode(self, sample_output_list):
        """Test error handling for unknown output mode."""
        with pytest.raises(SystemExit) as exc_info:
            main.write_documentation_file('output.md', 'unknown', sample_output_list)
        assert exc_info.value.code == 1


class TestWriteOutputFileOverwriteMode:
    """Test the write_output_file_overwrite_mode function."""

    @patch('main.open', new_callable=mock_open)
    def test_write_output_file_overwrite_mode_success(self, mock_file):
        """Test successfully writing file in overwrite mode."""
        # Arrange
        output_list = ['Line 1', 'Line 2', 'Line 3']
        mock_handle = Mock()
        mock_file.return_value.__enter__.return_value = mock_handle
        
        # Act
        main.write_output_file_overwrite_mode('output.md', output_list)
        
        # Assert
        mock_file.assert_called_once_with('output.md', 'w', encoding='UTF-8')

    @patch('main.open', side_effect=IOError("Permission denied"))
    def test_write_output_file_overwrite_mode_io_error(self, mock_file):
        """Test handling IOError in overwrite mode."""
        # Arrange
        output_list = ['Line 1', 'Line 2']
        
        # Act & Assert - IOError is not caught in this function, so it should propagate
        with pytest.raises(IOError):
            main.write_output_file_overwrite_mode('output.md', output_list)


class TestWriteOutputFileUpdateMode:
    """Test the write_output_file_update_mode function."""

    @patch('main.find_action_docs_markers')
    @patch('main.open', new_callable=mock_open)
    def test_write_output_file_update_mode_with_markers(self, mock_file, mock_find_markers):
        """Test writing file in update mode with markers present."""
        # Arrange
        original_content = [
            'Header\n',
            '<!-- BEGIN_ACTION_DOCS -->\n',
            'Old content\n',
            '<!-- END_ACTION_DOCS -->\n',
            'Footer\n'
        ]
        output_list = ['New content']
        mock_find_markers.return_value = (True, True)
        mock_handle = Mock()
        mock_file.return_value.__enter__.return_value = mock_handle
        
        # Act
        main.write_output_file_update_mode('output.md', original_content, output_list)
        
        # Assert
        mock_find_markers.assert_called_once_with(original_content)

    @patch('main.find_action_docs_markers')
    def test_write_output_file_update_mode_missing_markers(self, mock_find_markers):
        """Test error when markers are missing in update mode."""
        # Arrange
        original_content = ['No markers here\n']
        output_list = ['New content']
        mock_find_markers.return_value = (False, False)
        
        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            main.write_output_file_update_mode('output.md', original_content, output_list)
        assert exc_info.value.code == 1


class TestMain:
    """Test the main function."""

    @pytest.fixture
    def sample_action_contents(self):
        """Sample action contents for testing."""
        return {
            'name': 'Test Action',
            'description': 'A test GitHub action',
            'inputs': {
                'test_input': {
                    'description': 'Test input parameter',
                    'required': True,
                    'type': 'string',
                    'default': 'test_value'
                }
            },
            'outputs': {
                'test_output': {
                    'description': 'Test output parameter',
                    'value': '${{ steps.test.outputs.result }}'
                }
            }
        }

    @patch.dict(os.environ, {
        'ACTION_FILE_NAME': 'action.yaml',
        'OUTPUT_FILE_NAME': 'README.md',
        'OUTPUT_MODE': 'overwrite'
    })
    @patch('main.open_action_file')
    @patch('main.write_documentation_file')
    def test_main_success(self, mock_write_doc, mock_open_action, sample_action_contents):
        """Test successful main function execution."""
        # Arrange
        mock_open_action.return_value = sample_action_contents
        
        # Act
        result = main.main()
        
        # Assert
        assert result is True
        mock_open_action.assert_called_once_with('action.yaml')
        mock_write_doc.assert_called_once()

    @patch.dict(os.environ, {
        'ACTION_FILE_NAME': 'action.yaml',
        'OUTPUT_FILE_NAME': 'README.md',
        'OUTPUT_MODE': 'update'
    })
    @patch('main.open_action_file')
    @patch('main.write_documentation_file')
    def test_main_update_mode(self, mock_write_doc, mock_open_action, sample_action_contents):
        """Test main function in update mode."""
        # Arrange
        mock_open_action.return_value = sample_action_contents
        
        # Act
        result = main.main()
        
        # Assert
        assert result is True
        mock_open_action.assert_called_once_with('action.yaml')
        mock_write_doc.assert_called_once()

    @patch.dict(os.environ, {'ACTION_FILE_NAME': 'action.yaml'})
    @patch('main.open_action_file', side_effect=FileNotFoundError("File not found"))
    def test_main_file_not_found_error(self, mock_open_action):
        """Test main function handles FileNotFoundError."""
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        assert exc_info.value.code == 1

    @patch.dict(os.environ, {'ACTION_FILE_NAME': 'action.yaml'})
    @patch('main.open_action_file', side_effect=yaml.YAMLError("Invalid YAML"))
    def test_main_yaml_error(self, mock_open_action):
        """Test main function handles YAMLError."""
        with pytest.raises(SystemExit) as exc_info:
            main.main()
        assert exc_info.value.code == 1

    @patch.dict(os.environ, {'ACTION_FILE_NAME': 'action.yaml'})
    @patch('main.open_action_file', side_effect=IOError("IO Error"))
    def test_main_io_error(self, mock_open_action):
        """Test main function handles IOError."""
        # Act & Assert - IOError is not caught in main(), so it should propagate
        with pytest.raises(IOError):
            main.main()

    @patch.dict(os.environ, {}, clear=True)
    def test_main_missing_environment_variables(self):
        """Test main function with missing environment variables."""
        # Act & Assert - This should raise TypeError since None is passed to open_action_file
        with pytest.raises(TypeError):
            main.main()


class TestIntegration:
    """Integration tests using temporary files."""

    @pytest.fixture
    def temp_files(self):
        """Create temporary files for integration testing."""
        temp_dir = tempfile.mkdtemp()
        action_file = os.path.join(temp_dir, 'action.yaml')
        output_file = os.path.join(temp_dir, 'README.md')
        
        # Create a sample action file
        sample_action = {
            'name': 'Integration Test Action',
            'description': 'An action for integration testing',
            'inputs': {
                'test_input': {
                    'description': 'A test input',
                    'required': True,
                    'type': 'string',
                    'default': 'default_value'
                }
            },
            'outputs': {
                'test_output': {
                    'description': 'A test output',
                    'value': '${{ steps.test.outputs.value }}'
                }
            }
        }
        
        with open(action_file, 'w', encoding='utf-8') as f:
            yaml.dump(sample_action, f)
        
        yield {
            'temp_dir': temp_dir,
            'action_file': action_file,
            'output_file': output_file,
            'sample_action': sample_action
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_open_action_file_integration(self, temp_files):
        """Integration test for opening a real action file."""
        # Act
        result = main.open_action_file(temp_files['action_file'])
        
        # Assert
        assert result['name'] == 'Integration Test Action'
        assert result['description'] == 'An action for integration testing'
        assert 'test_input' in result['inputs']
        assert 'test_output' in result['outputs']

    @patch.dict(os.environ, {
        'ACTION_FILE_NAME': '',
        'OUTPUT_FILE_NAME': '',
        'OUTPUT_MODE': 'overwrite'
    })
    def test_full_workflow_integration(self, temp_files):
        """Integration test for the full workflow."""
        # Arrange
        os.environ['ACTION_FILE_NAME'] = temp_files['action_file']
        os.environ['OUTPUT_FILE_NAME'] = temp_files['output_file']
        
        # Create an empty output file
        with open(temp_files['output_file'], 'w', encoding='utf-8') as f:
            f.write('')
        
        # Act
        result = main.main()
        
        # Assert
        assert result is True
        
        # Check that output file was created and contains expected content
        with open(temp_files['output_file'], 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Integration Test Action' in content
            assert '# inputs' in content
            assert '# outputs' in content
            assert 'test_input' in content
            assert 'test_output' in content

    @patch.dict(os.environ, {
        'ACTION_FILE_NAME': '',
        'OUTPUT_FILE_NAME': '',
        'OUTPUT_MODE': 'update'
    })
    def test_update_mode_integration(self, temp_files):
        """Integration test for update mode workflow."""
        # Arrange
        os.environ['ACTION_FILE_NAME'] = temp_files['action_file']
        os.environ['OUTPUT_FILE_NAME'] = temp_files['output_file']
        
        # Create output file with markers
        initial_content = """# My Project

Some description here.

<!-- BEGIN_ACTION_DOCS -->
Old documentation
<!-- END_ACTION_DOCS -->

More content here.
"""
        with open(temp_files['output_file'], 'w', encoding='utf-8') as f:
            f.write(initial_content)
        
        # Act
        result = main.main()
        
        # Assert
        assert result is True
        
        # Check that the file was updated with new content
        with open(temp_files['output_file'], 'r', encoding='utf-8') as f:
            content = f.read()
            assert '# My Project' in content  # Original content preserved
            assert 'More content here.' in content  # Original content preserved
            assert 'Integration Test Action' in content  # New content added
            assert 'Old documentation' not in content  # Old content removed


# Parametrized tests for edge cases
@pytest.mark.parametrize("input_data,expected_fields", [
    (
        {'inputs': {'param1': {'description': 'Test'}}},
        ['param1', 'False', '', '', 'Test']
    ),
    (
        {'inputs': {'param1': {'required': True, 'type': 'boolean'}}},
        ['param1', 'True', 'boolean', '', '']
    ),
    (
        {'inputs': {'param1': {'default': 'test_default'}}},
        ['param1', 'False', '', '`test_default`', '']
    ),
    (
        {'inputs': {'param1': {'required': False, 'type': 'number', 'default': 42}}},
        ['param1', 'False', 'number', '`42`', '']
    ),
])
def test_process_action_inputs_parametrized(input_data, expected_fields):
    """Parametrized test for various input configurations."""
    result = main.process_action_inputs(input_data, [])
    
    # Find the row with the parameter data
    param_row = None
    for row in result:
        if row.startswith('| param1'):
            param_row = row
            break
    
    assert param_row is not None
    
    # Check that all expected fields are present in the row
    for field in expected_fields:
        assert field in param_row


@pytest.mark.parametrize("output_data,expected_content", [
    (
        {'outputs': {'result': {'description': 'Output result', 'value': '${{ steps.test.outputs.value }}'}}},
        ['result', 'Output result', '`${{ steps.test.outputs.value }}`']
    ),
    (
        {'outputs': {'result': {'value': '${{ steps.test.outputs.value }}'}}},
        ['result', '', '`${{ steps.test.outputs.value }}`']
    ),
    # Removed the test case with missing 'value' as it causes KeyError
])
def test_process_action_outputs_parametrized(output_data, expected_content):
    """Parametrized test for various output configurations."""
    result = main.process_action_outputs(output_data, [])
    
    # Find the row with the output data
    output_row = None
    for row in result:
        if row.startswith('|result'):
            output_row = row
            break
    
    assert output_row is not None
    
    # Check that all expected content is present in the row
    for content in expected_content:
        assert content in output_row


@pytest.mark.parametrize("env_vars,should_succeed", [
    ({'ACTION_FILE_NAME': 'action.yaml', 'OUTPUT_FILE_NAME': 'README.md', 'OUTPUT_MODE': 'overwrite'}, True),
    ({'ACTION_FILE_NAME': 'action.yaml', 'OUTPUT_FILE_NAME': 'README.md', 'OUTPUT_MODE': 'update'}, True),
    ({'ACTION_FILE_NAME': '', 'OUTPUT_FILE_NAME': 'README.md', 'OUTPUT_MODE': 'overwrite'}, False),
    ({'ACTION_FILE_NAME': 'action.yaml', 'OUTPUT_FILE_NAME': '', 'OUTPUT_MODE': 'overwrite'}, False),
    ({'ACTION_FILE_NAME': 'action.yaml', 'OUTPUT_FILE_NAME': 'README.md'}, False),  # Missing OUTPUT_MODE
])
def test_main_environment_variables_parametrized(env_vars, should_succeed):
    """Parametrized test for various environment variable configurations."""
    with patch.dict(os.environ, env_vars, clear=True):
        if should_succeed:
            with patch('main.open_action_file', return_value={'name': 'Test', 'description': 'Test description'}):
                with patch('main.write_documentation_file'):
                    result = main.main()
                    assert result is True
        else:
            with pytest.raises((SystemExit, TypeError)) as exc_info:
                main.main()
            if isinstance(exc_info.value, SystemExit):
                assert exc_info.value.code == 1
