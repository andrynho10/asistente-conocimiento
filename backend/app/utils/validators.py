"""
Password and input validation utilities for the authentication system.
Ensures compliance with security requirements including password complexity rules.
"""

import re
from typing import Tuple


def validate_password(password: str, username: str) -> Tuple[bool, str]:
    """
    Validate password against security requirements.

    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter (A-Z)
    - At least 1 lowercase letter (a-z)
    - At least 1 digit (0-9)
    - At least 1 special character (!@#$%^&*()_+-=[]{}|;:,.<>?)
    - Must not equal username

    Args:
        password: The password to validate
        username: The username for uniqueness check

    Returns:
        Tuple of (is_valid: bool, error_message: str)
        If is_valid is True, error_message is empty string
        If is_valid is False, error_message contains the reason why
    """
    # Check minimum length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    # Check if password equals username
    if password.lower() == username.lower():
        return False, "Password cannot be the same as username"

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    # Check for digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    # Check for special character
    special_char_pattern = r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]'
    if not re.search(special_char_pattern, password):
        return False, "Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)"

    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Basic email format validation.

    Args:
        email: The email address to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Simple regex pattern for email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not email or len(email) > 255:
        return False, "Email must be between 1 and 255 characters"

    if not re.match(email_pattern, email):
        return False, "Invalid email format"

    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.

    Requirements:
    - Length between 3 and 50 characters
    - Alphanumeric characters and underscores only
    - Cannot start with a digit

    Args:
        username: The username to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must not exceed 50 characters"

    # Check for valid characters (alphanumeric and underscore)
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
        return False, "Username must start with a letter and contain only alphanumeric characters and underscores"

    return True, ""
