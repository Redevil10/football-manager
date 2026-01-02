# tests/test_validation.py - Unit tests for validation helper functions

from core.validation import (
    parse_int,
    validate_in_list,
    validate_int_range,
    validate_non_empty_string,
    validate_required_fields,
    validate_required_int,
)


class TestValidateNonEmptyString:
    """Test validate_non_empty_string function"""

    def test_valid_string(self):
        """Test that valid non-empty strings pass validation"""
        is_valid, error_msg = validate_non_empty_string("test", "field")
        assert is_valid is True
        assert error_msg is None

    def test_string_with_whitespace(self):
        """Test that strings with only whitespace fail validation"""
        is_valid, error_msg = validate_non_empty_string("   ", "field")
        assert is_valid is False
        assert "cannot be empty" in error_msg.lower()

    def test_empty_string(self):
        """Test that empty strings fail validation"""
        is_valid, error_msg = validate_non_empty_string("", "field")
        assert is_valid is False
        assert "cannot be empty" in error_msg.lower()

    def test_none_value(self):
        """Test that None values fail validation"""
        is_valid, error_msg = validate_non_empty_string(None, "field")
        assert is_valid is False
        assert "required" in error_msg.lower()

    def test_non_string_type(self):
        """Test that non-string types fail validation"""
        is_valid, error_msg = validate_non_empty_string(123, "field")
        assert is_valid is False
        assert "must be a string" in error_msg.lower()

    def test_custom_field_name(self):
        """Test that custom field names appear in error messages"""
        is_valid, error_msg = validate_non_empty_string("", "username")
        assert is_valid is False
        assert "username" in error_msg.lower()


class TestValidateRequiredFields:
    """Test validate_required_fields function"""

    def test_all_fields_present(self):
        """Test that all required fields present pass validation"""
        form_data = {
            "username": "test",
            "password": "secret",
            "email": "test@example.com",
        }
        is_valid, error_msg = validate_required_fields(
            form_data, ["username", "password", "email"]
        )
        assert is_valid is True
        assert error_msg is None

    def test_missing_field(self):
        """Test that missing required fields fail validation"""
        form_data = {"username": "test", "password": "secret"}
        is_valid, error_msg = validate_required_fields(
            form_data, ["username", "password", "email"]
        )
        assert is_valid is False
        assert "email" in error_msg.lower()

    def test_empty_field(self):
        """Test that empty required fields fail validation"""
        form_data = {"username": "test", "password": "", "email": "test@example.com"}
        is_valid, error_msg = validate_required_fields(
            form_data, ["username", "password", "email"]
        )
        assert is_valid is False
        assert "password" in error_msg.lower()

    def test_whitespace_only_field(self):
        """Test that whitespace-only fields fail validation"""
        form_data = {"username": "   ", "password": "secret"}
        is_valid, error_msg = validate_required_fields(
            form_data, ["username", "password"]
        )
        assert is_valid is False
        assert "username" in error_msg.lower()


class TestParseInt:
    """Test parse_int function"""

    def test_valid_integer_string(self):
        """Test parsing valid integer strings"""
        value, error_msg = parse_int("123", "field")
        assert value == 123
        assert error_msg is None

    def test_negative_integer(self):
        """Test parsing negative integers"""
        value, error_msg = parse_int("-42", "field")
        assert value == -42
        assert error_msg is None

    def test_zero(self):
        """Test parsing zero"""
        value, error_msg = parse_int("0", "field")
        assert value == 0
        assert error_msg is None

    def test_whitespace_around_number(self):
        """Test that whitespace is stripped"""
        value, error_msg = parse_int("  42  ", "field")
        assert value == 42
        assert error_msg is None

    def test_none_value_with_default(self):
        """Test that None values return default"""
        value, error_msg = parse_int(None, "field", default=10)
        assert value == 10
        assert error_msg is None

    def test_empty_string_with_default(self):
        """Test that empty strings return default"""
        value, error_msg = parse_int("", "field", default=5)
        assert value == 5
        assert error_msg is None

    def test_none_value_without_default(self):
        """Test that None values without default return None"""
        value, error_msg = parse_int(None, "field")
        assert value is None
        assert error_msg is None

    def test_invalid_string(self):
        """Test that invalid strings return error"""
        value, error_msg = parse_int("abc", "field")
        assert value is None
        assert "must be a valid integer" in error_msg.lower()

    def test_float_string(self):
        """Test that float strings return error"""
        value, error_msg = parse_int("3.14", "field")
        assert value is None
        assert "must be a valid integer" in error_msg.lower()

    def test_non_string_type(self):
        """Test that non-string types are converted"""
        value, error_msg = parse_int(123, "field")
        assert value == 123
        assert error_msg is None


class TestValidateIntRange:
    """Test validate_int_range function"""

    def test_value_within_range(self):
        """Test that values within range pass validation"""
        is_valid, error_msg = validate_int_range(
            50, min_value=0, max_value=100, field_name="field"
        )
        assert is_valid is True
        assert error_msg is None

    def test_value_at_minimum(self):
        """Test that values at minimum pass validation"""
        is_valid, error_msg = validate_int_range(
            0, min_value=0, max_value=100, field_name="field"
        )
        assert is_valid is True
        assert error_msg is None

    def test_value_at_maximum(self):
        """Test that values at maximum pass validation"""
        is_valid, error_msg = validate_int_range(
            100, min_value=0, max_value=100, field_name="field"
        )
        assert is_valid is True
        assert error_msg is None

    def test_value_below_minimum(self):
        """Test that values below minimum fail validation"""
        is_valid, error_msg = validate_int_range(
            -1, min_value=0, max_value=100, field_name="field"
        )
        assert is_valid is False
        assert "at least" in error_msg.lower()

    def test_value_above_maximum(self):
        """Test that values above maximum fail validation"""
        is_valid, error_msg = validate_int_range(
            101, min_value=0, max_value=100, field_name="field"
        )
        assert is_valid is False
        assert "at most" in error_msg.lower()

    def test_only_minimum(self):
        """Test validation with only minimum specified"""
        is_valid, error_msg = validate_int_range(10, min_value=0, field_name="field")
        assert is_valid is True
        assert error_msg is None

    def test_only_maximum(self):
        """Test validation with only maximum specified"""
        is_valid, error_msg = validate_int_range(10, max_value=100, field_name="field")
        assert is_valid is True
        assert error_msg is None

    def test_no_bounds(self):
        """Test validation with no bounds specified"""
        is_valid, error_msg = validate_int_range(10, field_name="field")
        assert is_valid is True
        assert error_msg is None

    def test_non_integer_type(self):
        """Test that non-integer types fail validation"""
        is_valid, error_msg = validate_int_range("10", field_name="field")
        assert is_valid is False
        assert "must be an integer" in error_msg.lower()


class TestValidateInList:
    """Test validate_in_list function"""

    def test_valid_value_in_list(self):
        """Test that valid values in list pass validation"""
        valid_values = ["viewer", "manager"]
        is_valid, error_msg = validate_in_list("viewer", valid_values, "role")
        assert is_valid is True
        assert error_msg is None

    def test_value_not_in_list(self):
        """Test that values not in list fail validation"""
        valid_values = ["viewer", "manager"]
        is_valid, error_msg = validate_in_list("admin", valid_values, "role")
        assert is_valid is False
        assert "must be one of" in error_msg.lower()
        assert "viewer" in error_msg
        assert "manager" in error_msg

    def test_empty_string(self):
        """Test that empty strings fail validation"""
        valid_values = ["viewer", "manager"]
        is_valid, error_msg = validate_in_list("", valid_values, "role")
        assert is_valid is False
        assert "cannot be empty" in error_msg.lower()

    def test_whitespace_only(self):
        """Test that whitespace-only strings fail validation"""
        valid_values = ["viewer", "manager"]
        is_valid, error_msg = validate_in_list("   ", valid_values, "role")
        assert is_valid is False
        assert "cannot be empty" in error_msg.lower()

    def test_none_value(self):
        """Test that None values fail validation"""
        valid_values = ["viewer", "manager"]
        is_valid, error_msg = validate_in_list(None, valid_values, "role")
        assert is_valid is False
        assert "required" in error_msg.lower()

    def test_non_string_type(self):
        """Test that non-string types are converted"""
        valid_values = ["1", "2", "3"]
        is_valid, error_msg = validate_in_list(1, valid_values, "field")
        assert is_valid is True
        assert error_msg is None

    def test_case_sensitive(self):
        """Test that validation is case-sensitive"""
        valid_values = ["viewer", "manager"]
        is_valid, error_msg = validate_in_list("Viewer", valid_values, "role")
        assert is_valid is False
        assert "must be one of" in error_msg.lower()


class TestValidateRequiredInt:
    """Test validate_required_int function"""

    def test_valid_integer(self):
        """Test that valid integers pass validation"""
        value, error_msg = validate_required_int("42", "field")
        assert value == 42
        assert error_msg is None

    def test_valid_integer_with_range(self):
        """Test that valid integers within range pass validation"""
        value, error_msg = validate_required_int(
            "50", "field", min_value=0, max_value=100
        )
        assert value == 50
        assert error_msg is None

    def test_integer_at_minimum(self):
        """Test that integers at minimum pass validation"""
        value, error_msg = validate_required_int(
            "0", "field", min_value=0, max_value=100
        )
        assert value == 0
        assert error_msg is None

    def test_integer_at_maximum(self):
        """Test that integers at maximum pass validation"""
        value, error_msg = validate_required_int(
            "100", "field", min_value=0, max_value=100
        )
        assert value == 100
        assert error_msg is None

    def test_empty_string(self):
        """Test that empty strings fail validation"""
        value, error_msg = validate_required_int("", "field")
        assert value is None
        assert "cannot be empty" in error_msg.lower()

    def test_none_value(self):
        """Test that None values fail validation"""
        value, error_msg = validate_required_int(None, "field")
        assert value is None
        # validate_non_empty_string returns "is required" for None values
        assert "required" in error_msg.lower()

    def test_invalid_string(self):
        """Test that invalid strings fail validation"""
        value, error_msg = validate_required_int("abc", "field")
        assert value is None
        assert "must be a valid integer" in error_msg.lower()

    def test_below_minimum(self):
        """Test that values below minimum fail validation"""
        value, error_msg = validate_required_int("-1", "field", min_value=0)
        assert value is None
        assert "at least" in error_msg.lower()

    def test_above_maximum(self):
        """Test that values above maximum fail validation"""
        value, error_msg = validate_required_int("101", "field", max_value=100)
        assert value is None
        assert "at most" in error_msg.lower()

    def test_whitespace_handling(self):
        """Test that whitespace is properly handled"""
        value, error_msg = validate_required_int("  42  ", "field")
        assert value == 42
        assert error_msg is None
