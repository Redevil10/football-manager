# validation.py - Input validation helper functions

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def validate_non_empty_string(
    value: Optional[str], field_name: str = "field"
) -> Tuple[bool, Optional[str]]:
    """Validate that a string value is not empty after stripping.

    Args:
        value: The value to validate (can be None)
        field_name: Name of the field for error messages

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"

    if not isinstance(value, str):
        return False, f"{field_name} must be a string"

    stripped = value.strip()
    if not stripped:
        return False, f"{field_name} cannot be empty"

    return True, None


def validate_required_fields(
    form_data: dict, required_fields: list[str]
) -> Tuple[bool, Optional[str]]:
    """Validate that all required fields are present and non-empty.

    Args:
        form_data: Dictionary of form data
        required_fields: List of required field names

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, error_message)
    """
    for field in required_fields:
        value = form_data.get(field)
        is_valid, error_msg = validate_non_empty_string(value, field)
        if not is_valid:
            return False, error_msg

    return True, None


def parse_int(
    value: Optional[str], field_name: str = "field", default: Optional[int] = None
) -> Tuple[Optional[int], Optional[str]]:
    """Parse a string to an integer with validation.

    Args:
        value: The value to parse (can be None or empty string)
        field_name: Name of the field for error messages
        default: Default value to return if value is None or empty (optional)

    Returns:
        Tuple[Optional[int], Optional[str]]: (parsed_value, error_message)
        - If successful: (int_value, None)
        - If value is None/empty and default provided: (default, None)
        - If value is None/empty and no default: (None, None)
        - If parsing fails: (None, error_message)
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        if default is not None:
            return default, None
        return None, None

    try:
        return int(str(value).strip()), None
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse {field_name} as integer: {value} - {e}")
        return None, f"{field_name} must be a valid integer"


def validate_int_range(
    value: int,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
    field_name: str = "field",
) -> Tuple[bool, Optional[str]]:
    """Validate that an integer is within a specified range.

    Args:
        value: The integer value to validate
        min_value: Minimum allowed value (inclusive, optional)
        max_value: Maximum allowed value (inclusive, optional)
        field_name: Name of the field for error messages

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, error_message)
    """
    if not isinstance(value, int):
        return False, f"{field_name} must be an integer"

    if min_value is not None and value < min_value:
        return False, f"{field_name} must be at least {min_value}"

    if max_value is not None and value > max_value:
        return False, f"{field_name} must be at most {max_value}"

    return True, None


def validate_in_list(
    value: Optional[str], valid_values: list[str], field_name: str = "field"
) -> Tuple[bool, Optional[str]]:
    """Validate that a value is in a list of valid values.

    Args:
        value: The value to validate (can be None)
        valid_values: List of valid string values
        field_name: Name of the field for error messages

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
        - If valid: (True, None)
        - If invalid: (False, error_message)
    """
    if value is None:
        return False, f"{field_name} is required"

    if not isinstance(value, str):
        value = str(value)

    stripped = value.strip()
    if not stripped:
        return False, f"{field_name} cannot be empty"

    if stripped not in valid_values:
        return False, f"{field_name} must be one of: {', '.join(valid_values)}"

    return True, None


def validate_required_int(
    value: Optional[str],
    field_name: str = "field",
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> Tuple[Optional[int], Optional[str]]:
    """Validate and parse a required integer field.

    This is a convenience function that combines parse_int and validate_int_range
    for required integer fields.

    Args:
        value: The value to parse and validate (required, cannot be None/empty)
        field_name: Name of the field for error messages
        min_value: Minimum allowed value (inclusive, optional)
        max_value: Maximum allowed value (inclusive, optional)

    Returns:
        Tuple[Optional[int], Optional[str]]: (parsed_value, error_message)
        - If successful: (int_value, None)
        - If parsing/validation fails: (None, error_message)
    """
    # First check if value is present
    is_valid, error_msg = validate_non_empty_string(value, field_name)
    if not is_valid:
        return None, error_msg

    # Parse to integer
    parsed_value, parse_error = parse_int(value, field_name)
    if parse_error:
        return None, parse_error

    if parsed_value is None:
        return None, f"{field_name} is required"

    # Validate range if specified
    if min_value is not None or max_value is not None:
        range_valid, range_error = validate_int_range(
            parsed_value, min_value, max_value, field_name
        )
        if not range_valid:
            return None, range_error

    return parsed_value, None
