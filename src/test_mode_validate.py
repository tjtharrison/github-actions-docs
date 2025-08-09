"""Tests for mode_validate.py functions."""

import io
import sys
from unittest.mock import patch

import pytest

import mode_validate


class TestModeValidate:
    """Test the main function in mode_validate.py."""

    def test_main_valid_update_mode(self, capsys):
        """Test main function with valid 'update' mode."""
        # Arrange
        test_args = ['mode_validate.py', 'update']
        
        with patch.object(sys, 'argv', test_args):
            # Act
            result = mode_validate.main(test_args)
            
            # Assert
            assert result is True
            captured = capsys.readouterr()
            assert "update mode set" in captured.out

    def test_main_valid_overwrite_mode(self, capsys):
        """Test main function with valid 'overwrite' mode."""
        # Arrange
        test_args = ['mode_validate.py', 'overwrite']
        
        with patch.object(sys, 'argv', test_args):
            # Act
            result = mode_validate.main(test_args)
            
            # Assert
            assert result is True
            captured = capsys.readouterr()
            assert "overwrite mode set" in captured.out

    def test_main_invalid_mode(self, capsys):
        """Test main function with invalid mode."""
        # Arrange
        test_args = ['mode_validate.py', 'invalid_mode']
        
        with patch.object(sys, 'argv', test_args):
            # Act & Assert
            with pytest.raises(SystemExit) as exc_info:
                mode_validate.main(test_args)
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Provided value invalid_mode not in ['update', 'overwrite']" in captured.out

    def test_main_no_arguments(self, capsys):
        """Test main function with no mode argument provided."""
        # Arrange
        test_args = ['mode_validate.py']
        
        # Act
        result = mode_validate.main(test_args)
        
        # Assert
        assert result is True
        captured = capsys.readouterr()
        assert "Requires input" in captured.out

    def test_main_empty_arguments(self, capsys):
        """Test main function with empty arguments list."""
        # Arrange
        test_args = []
        
        # Act
        result = mode_validate.main(test_args)
        
        # Assert
        assert result is True
        captured = capsys.readouterr()
        assert "Requires input" in captured.out

    @pytest.mark.parametrize("mode,expected_output", [
        ("update", "update mode set"),
        ("overwrite", "overwrite mode set"),
    ])
    def test_main_parametrized_valid_modes(self, mode, expected_output, capsys):
        """Parametrized test for valid modes."""
        # Arrange
        test_args = ['mode_validate.py', mode]
        
        with patch.object(sys, 'argv', test_args):
            # Act
            result = mode_validate.main(test_args)
            
            # Assert
            assert result is True
            captured = capsys.readouterr()
            assert expected_output in captured.out

    @pytest.mark.parametrize("invalid_mode", [
        "append",
        "replace",
        "insert",
        "delete",
        "modify",
        "UPDATE",  # Case sensitive
        "OVERWRITE",  # Case sensitive
        "123",
        "",
        "update-mode",
    ])
    def test_main_parametrized_invalid_modes(self, invalid_mode, capsys):
        """Parametrized test for invalid modes."""
        # Arrange
        test_args = ['mode_validate.py', invalid_mode]
        
        with patch.object(sys, 'argv', test_args):
            # Act & Assert
            with pytest.raises(SystemExit) as exc_info:
                mode_validate.main(test_args)
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert f"Provided value {invalid_mode} not in ['update', 'overwrite']" in captured.out

    def test_main_multiple_arguments(self, capsys):
        """Test main function with multiple arguments (only first mode argument should be used)."""
        # Arrange
        test_args = ['mode_validate.py', 'update', 'extra', 'arguments']
        
        with patch.object(sys, 'argv', test_args):
            # Act
            result = mode_validate.main(test_args)
            
            # Assert
            assert result is True
            captured = capsys.readouterr()
            assert "update mode set" in captured.out

    def test_main_with_special_characters(self, capsys):
        """Test main function with special characters in mode."""
        # Arrange
        test_args = ['mode_validate.py', 'up@date']
        
        with patch.object(sys, 'argv', test_args):
            # Act & Assert
            with pytest.raises(SystemExit) as exc_info:
                mode_validate.main(test_args)
            
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "Provided value up@date not in ['update', 'overwrite']" in captured.out
