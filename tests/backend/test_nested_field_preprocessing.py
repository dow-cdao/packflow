"""
Test suite for nested field preprocessing with delimiter handling.

This test file verifies the fix for the delimiter handling issue:
- When flatten_nested_inputs=False and no nested paths are accessed via delimiter notation,
  keys containing delimiters should be preserved as-is, not split into nested structures.
- When nested paths ARE accessed via delimiter notation in rename_fields or feature_names,
  the preprocessor should correctly access those paths.

These tests will pass once the fix is implemented.
"""

from packflow.backend.configuration import BackendConfig
from packflow.backend.preprocessors import RecordsPreprocessor


class TestDelimiterPreservation:
    """Tests verifying that keys containing delimiters are preserved when not accessed as nested paths.
    
    These tests specify the correct behavior after the fix is implemented.
    """

    def test_preserve_delimiter_in_nested_key_with_rename_fields(self):
        """
        When flatten_nested_inputs=False and rename_fields doesn't use nested paths,
        keys containing delimiters should be preserved as-is.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"x": "y"}  # Flat key, no nested path access
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": {"c:d": 100}}, "x": 5}]
        result = preprocessor(input_data)
        
        # DESIRED: "c:d" should be preserved as single key
        assert "a" in result[0]
        assert "b" in result[0]["a"]
        assert "c:d" in result[0]["a"]["b"]
        assert result[0]["a"]["b"]["c:d"] == 100
        assert result[0]["y"] == 5

    def test_preserve_delimiter_in_nested_key_no_path_access(self):
        """
        When flatten_nested_inputs=False and no nested paths are accessed,
        keys containing delimiters should be preserved.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            rename_fields={"x": "y"}  # Flat key, no nested path access
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"data": {"field.name": 42}, "x": 1}]
        result = preprocessor(input_data)
        
        # DESIRED: "field.name" should be preserved as single key
        assert "data" in result[0]
        assert "field.name" in result[0]["data"]
        assert result[0]["data"]["field.name"] == 42
        assert result[0]["y"] == 1

    def test_preserve_multiple_delimiter_levels(self):
        """
        Multiple nested keys containing delimiters should all be preserved.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            rename_fields={"dummy": "dummy2"}
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b.c": {"d.e": 100}}}]
        result = preprocessor(input_data)
        
        # DESIRED: Both "b.c" and "d.e" should be preserved as single keys
        assert "a" in result[0]
        assert "b.c" in result[0]["a"]
        assert "d.e" in result[0]["a"]["b.c"]
        assert result[0]["a"]["b.c"]["d.e"] == 100


class TestNestedPathAccess:
    """
    Tests verifying that nested paths CAN be accessed via delimiter notation.
    
    These tests verify that when rename_fields or feature_names DO use delimiter notation
    to access nested paths, the preprocessor correctly accesses those paths.
    These tests should continue to pass after the fix.
    """

    def test_nested_path_in_rename_fields(self):
        """
        Verify that rename_fields can access nested paths using delimiter notation.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"a:b": "feature_1"}  # Nested path - needs flattening
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": 10, "c": 20}}]
        result = preprocessor(input_data)
        
        # Should correctly access a:b and rename it
        assert "feature_1" in result[0]
        assert result[0]["feature_1"] == 10

    def test_nested_path_in_feature_names(self):
        """
        Verify that feature_names can access nested paths using delimiter notation.
        When flatten_nested_inputs=False, output should preserve nested structure.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            feature_names=["data.value"]  # Nested path access
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"data": {"value": 42, "other": 99}}]
        result = preprocessor(input_data)
        
        # Should correctly access data.value and return nested structure
        assert "data" in result[0]
        assert "value" in result[0]["data"]
        assert result[0]["data"]["value"] == 42


    def test_mixed_nested_and_flat_rename_fields(self):
        """
        Verify correct handling of mixed flat and nested paths in rename_fields.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={
                "x": "feature_0",  # Flat
                "a:b": "feature_1"  # Nested path
            }
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"x": 1, "a": {"b": 2, "c": 3}}]
        result = preprocessor(input_data)
        
        assert result[0]["feature_0"] == 1
        assert result[0]["feature_1"] == 2

    def test_mixed_nested_and_flat_feature_names(self):
        """
        Verify correct handling of mixed flat and nested paths in feature_names.
        When flatten_nested_inputs=False, output should preserve nested structure.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            feature_names=["x", "a.b"]  # Mixed
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"x": 1, "a": {"b": 2, "c": 3}}]
        result = preprocessor(input_data)
        
        assert result[0]["x"] == 1
        assert "a" in result[0]
        assert "b" in result[0]["a"]
        assert result[0]["a"]["b"] == 2

    def test_missing_nested_keys(self):
        """
        Verify that missing nested keys are handled gracefully.
        New behavior: missing paths are skipped and not included in output.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            feature_names=["a:b:c"]  # Path doesn't exist
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": 10}}]  # Missing "c"
        result = preprocessor(input_data)
        
        # Should return empty dict since the path doesn't exist
        assert result[0] == {}

    def test_none_values_in_paths(self):
        """
        Verify that None values in nested paths are handled gracefully.
        New behavior: paths that resolve to None are skipped.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            feature_names=["a:b"]
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": None}]
        result = preprocessor(input_data)
        
        # Should return empty dict since the path resolves to None
        assert result[0] == {}

    def test_flatten_lists_interaction(self):
        """
        Verify correct interaction with flatten_lists configuration.
        """
        config = BackendConfig(
            flatten_nested_inputs=True,
            flatten_lists=True,
            nested_field_delimiter=":",
            feature_names=["a:b:0"]
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": [10, 20, 30]}}]
        result = preprocessor(input_data)
        
        assert "a:b:0" in result[0]
        assert result[0]["a:b:0"] == 10

    def test_deeply_nested_path_access(self):
        """
        Verify correct handling of deeply nested path access.
        When flatten_nested_inputs=False, output should preserve nested structure.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            feature_names=["a.b.c.d.e"]
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": {"c": {"d": {"e": 999}}}}}]
        result = preprocessor(input_data)
        
        assert result[0]["a"]["b"]["c"]["d"]["e"] == 999

    def test_empty_dict_values(self):
        """
        Verify correct handling of empty dictionaries in nested structures.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"x": "y"}
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {}, "x": 1}]
        result = preprocessor(input_data)
        
        assert result[0]["a"] == {}
        assert result[0]["y"] == 1

    def test_no_feature_names_with_nested_structure(self):
        """
        Verify that entire nested structure is preserved when no feature_names specified.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"x": "y"}
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": {"c": 1}}, "x": 2}]
        result = preprocessor(input_data)
        
        # Should preserve full nested structure
        assert result[0]["a"]["b"]["c"] == 1
        assert result[0]["y"] == 2

    def test_delimiter_in_top_level_key_raises_error(self):
        """
        Verify that when a top-level key contains the delimiter and we're using nested paths,
        an error is raised by default to prevent ambiguity.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"a:b": "feature"}  # This triggers nested path access
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a:b": 100}]  # Top-level key with delimiter - collision!
        
        # Should raise an error about delimiter collision
        import pytest
        from packflow.exceptions import PreprocessorRuntimeError
        with pytest.raises(PreprocessorRuntimeError, match="Keys containing the delimiter"):
            preprocessor(input_data)
    
    def test_delimiter_in_top_level_key_with_ignore(self):
        """
        Verify that with ignore_delimiter_collisions=True, keys with delimiters are handled.
        The literal key "a:b" is checked first and found, so it gets renamed.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"a:b": "feature"},
            feature_names=["feature"],  # Specify feature_names to filter output
            ignore_delimiter_collisions=True
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a:b": 100}]  # Top-level key with delimiter
        result = preprocessor(input_data)
        
        # The literal key "a:b" is checked first and found, so it gets renamed
        # Only "feature" is included because feature_names filters the output
        assert result[0] == {"feature": 100}

    def test_partial_missing_paths(self):
        """
        Verify that when some paths exist and some don't, only existing ones are included.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            feature_names=["a.b", "c.d", "e.f"]  # Only a.b and e.f exist
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": 1}, "e": {"f": 3}}]  # Missing c.d
        result = preprocessor(input_data)
        
        # Should only include the paths that exist
        assert "a" in result[0]
        assert "b" in result[0]["a"]
        assert result[0]["a"]["b"] == 1
        assert "e" in result[0]
        assert "f" in result[0]["e"]
        assert result[0]["e"]["f"] == 3
        # c.d should not be present
        assert "c" not in result[0]



class TestEdgeCases:
    """Additional edge cases for robustness."""

    def test_empty_input_list(self):
        """Handle empty input list."""
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"a": "b"}
        )
        preprocessor = RecordsPreprocessor(config)
        
        result = preprocessor([])
        assert result == []

    def test_multiple_records_preserves_delimiters(self):
        """Ensure processing works correctly for multiple records and preserves delimiter keys."""
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=":",
            rename_fields={"x": "y"}  # No nested path access
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [
            {"a": {"b:c": 1}, "x": 10},
            {"a": {"b:c": 2}, "x": 20},
            {"a": {"b:c": 3}, "x": 30},
        ]
        result = preprocessor(input_data)
        
        assert len(result) == 3
        for i, record in enumerate(result):
            # "b:c" is preserved as single key since we're not using nested paths
            assert record["a"]["b:c"] == i + 1
            assert record["y"] == (i + 1) * 10
    
    def test_delimiter_collision_detection(self):
        """Test that delimiter collisions are detected when using nested paths."""
        import pytest
        from packflow.exceptions import PreprocessorRuntimeError
        
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            feature_names=["a.b"]  # Using nested path access
        )
        preprocessor = RecordsPreprocessor(config)
        
        # Input has a key containing the delimiter
        input_data = [{"field.name": 42, "a": {"b": 1}}]
        
        with pytest.raises(PreprocessorRuntimeError, match="Keys containing the delimiter"):
            preprocessor(input_data)

    def test_unicode_in_keys_and_delimiters(self):
        """Handle unicode characters in keys and delimiters.
        When flatten_nested_inputs=False, output should be nested structure.
        """
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter="→",
            feature_names=["a→b"]
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": 42}}]
        result = preprocessor(input_data)
        
        assert "a" in result[0]
        assert "b" in result[0]["a"]
        assert result[0]["a"]["b"] == 42

    def test_special_characters_in_keys(self):
        """Handle special characters in keys."""
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            rename_fields={"x": "y"}
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b@c#d": 100}, "x": 1}]
        result = preprocessor(input_data)
        
        assert result[0]["a"]["b@c#d"] == 100


class TestFlattenedOutput:
    """Tests for when flatten_nested_inputs=True (flattened output format)."""

    def test_flatten_nested_inputs_with_feature_names(self):
        """When flatten_nested_inputs=True, output should be flattened."""
        config = BackendConfig(
            flatten_nested_inputs=True,
            nested_field_delimiter=":",
            feature_names=["a:b"]
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": 10}}]
        result = preprocessor(input_data)
        
        assert result[0] == {"a:b": 10}
    
    def test_flatten_mode_with_missing_rename_field(self):
        """Test flatten mode when rename_fields references a missing key (value is None)."""
        config = BackendConfig(
            flatten_nested_inputs=True,
            nested_field_delimiter=".",
            rename_fields={"missing.key": "renamed"}
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": 10}}]
        result = preprocessor(input_data)
        
        # Missing key should be skipped (not included in output)
        assert result[0] == {"a.b": 10}
    
    def test_flatten_mode_with_existing_rename_field(self):
        """Test flatten mode when rename_fields references an existing key."""
        config = BackendConfig(
            flatten_nested_inputs=True,
            nested_field_delimiter=".",
            rename_fields={"a.b": "renamed_field"},
            feature_names=["renamed_field", "a.c"]  # Filter to only these fields
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"a": {"b": 10, "c": 20}}]
        result = preprocessor(input_data)
        
        # Existing key should be renamed and filtered
        assert result[0] == {"renamed_field": 10, "a.c": 20}


class TestRenameFieldsWithNestedDelimiter:
    """Tests for rename_fields where the target key contains the delimiter."""
    
    def test_rename_to_nested_path(self):
        """Test renaming a field to a nested path (target contains delimiter)."""
        config = BackendConfig(
            flatten_nested_inputs=False,
            nested_field_delimiter=".",
            rename_fields={"x": "a.b.c"},  # Rename x to nested path a.b.c
            feature_names=["a.b.c"]
        )
        preprocessor = RecordsPreprocessor(config)
        
        input_data = [{"x": 100}]
        result = preprocessor(input_data)
        
        # Should create nested structure for the renamed field
        assert result[0] == {"a": {"b": {"c": 100}}}


class TestSetNestedFieldEdgeCases:
    """Tests for set_nested_field_direct edge cases."""
    
    def test_set_nested_field_blocked_by_non_dict(self):
        """Test that set_nested_field_direct handles non-dict values in path gracefully."""
        from packflow.utils import set_nested_field_direct
        
        obj = {"a": "string_value"}  # 'a' is a string, not a dict
        
        # Try to set a.b.c when 'a' is not a dict
        set_nested_field_direct(obj, "a.b.c", 100, ".")
        
        # Should not crash, and 'a' should remain unchanged
        assert obj == {"a": "string_value"}


class TestGetNestedFieldLiteralKey:
    """Tests for get_nested_field when field exists as literal key."""
    
    def test_get_nested_field_literal_key_priority(self):
        """Test that literal keys take priority over nested path interpretation."""
        from packflow.utils import get_nested_field
        
        # Object has both a literal key "a.b" and a nested structure a -> b
        obj = {
            "a.b": 100,
            "a": {"b": 200}
        }
        
        # get_nested_field should return the literal key first
        result = get_nested_field(obj, "a.b", ".")
        assert result == 100
