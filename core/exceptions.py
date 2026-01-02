# exceptions.py - Custom exception classes for standardized error handling

"""Custom exceptions for the Football Manager application.

These exceptions provide a standardized way to handle errors across the application,
making it easier to distinguish between different types of failures and provide
appropriate error messages to users.
"""


class DatabaseError(Exception):
    """Base exception for database-related errors"""

    pass


class IntegrityError(DatabaseError):
    """Raised when a database integrity constraint is violated.

    This typically occurs when trying to insert duplicate records or
    violate foreign key constraints.

    Attributes:
        message: Human-readable error message
        operation: The operation that failed (e.g., "create_user", "add_player")
        details: Additional error details
    """

    def __init__(self, message: str, operation: str = None, details: str = None):
        self.message = message
        self.operation = operation
        self.details = details
        super().__init__(self.message)


class NotFoundError(DatabaseError):
    """Raised when a requested record is not found.

    Attributes:
        resource_type: Type of resource not found (e.g., "user", "club", "match")
        resource_id: ID of the resource that was not found
    """

    def __init__(self, resource_type: str, resource_id: int = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        if resource_id is not None:
            message = f"{resource_type.capitalize()} with ID {resource_id} not found"
        else:
            message = f"{resource_type.capitalize()} not found"
        super().__init__(message)


class ValidationError(Exception):
    """Raised when input validation fails.

    Attributes:
        field: Name of the field that failed validation
        message: Human-readable error message
    """

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class PermissionError(Exception):
    """Raised when a user doesn't have permission to perform an action.

    Attributes:
        action: The action that was attempted
        resource: The resource the action was attempted on
    """

    def __init__(self, action: str, resource: str = None):
        self.action = action
        self.resource = resource
        if resource:
            message = f"Permission denied: Cannot {action} {resource}"
        else:
            message = f"Permission denied: Cannot {action}"
        super().__init__(message)
