"""
Unit tests for password validation utilities.
Tests the validate_password function against security requirements.
"""

import pytest
from app.utils.validators import validate_password, validate_email, validate_username


class TestValidatePassword:
    """Test cases for password validation."""

    def test_valid_password(self):
        """Test a password that meets all requirements."""
        is_valid, msg = validate_password("ValidPass123!", "testuser")
        assert is_valid is True
        assert msg == ""

    def test_password_too_short(self):
        """Test that password shorter than 8 characters is rejected."""
        is_valid, msg = validate_password("Short1!", "testuser")
        assert is_valid is False
        assert "at least 8 characters" in msg

    def test_password_no_uppercase(self):
        """Test that password without uppercase letter is rejected."""
        is_valid, msg = validate_password("password123!", "testuser")
        assert is_valid is False
        assert "uppercase" in msg

    def test_password_no_lowercase(self):
        """Test that password without lowercase letter is rejected."""
        is_valid, msg = validate_password("PASSWORD123!", "testuser")
        assert is_valid is False
        assert "lowercase" in msg

    def test_password_no_digit(self):
        """Test that password without digit is rejected."""
        is_valid, msg = validate_password("PasswordABC!", "testuser")
        assert is_valid is False
        assert "digit" in msg

    def test_password_no_special_character(self):
        """Test that password without special character is rejected."""
        is_valid, msg = validate_password("Password123", "testuser")
        assert is_valid is False
        assert "special character" in msg

    def test_password_equals_username(self):
        """Test that password cannot equal username."""
        is_valid, msg = validate_password("TestPass123!", "TestPass123!")
        assert is_valid is False
        assert "same as username" in msg

    def test_password_case_insensitive_username_match(self):
        """Test that username comparison is case-insensitive."""
        is_valid, msg = validate_password("testpass123!", "TestPass123!")
        assert is_valid is False
        assert "same as username" in msg

    def test_password_with_various_special_chars(self):
        """Test that various special characters are accepted."""
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        for char in special_chars:
            password = f"ValidPass123{char}"
            is_valid, msg = validate_password(password, "testuser")
            assert is_valid is True, f"Failed for special char: {char}"

    def test_minimum_valid_password(self):
        """Test the minimum valid password (8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special)."""
        is_valid, msg = validate_password("Apasswd1!", "testuser")
        assert is_valid is True
        assert msg == ""


class TestValidateEmail:
    """Test cases for email validation."""

    def test_valid_email(self):
        """Test a valid email address."""
        is_valid, msg = validate_email("user@example.com")
        assert is_valid is True
        assert msg == ""

    def test_valid_email_with_subdomain(self):
        """Test email with subdomain."""
        is_valid, msg = validate_email("user@mail.example.co.uk")
        assert is_valid is True

    def test_invalid_email_no_at(self):
        """Test email without @ symbol."""
        is_valid, msg = validate_email("userexample.com")
        assert is_valid is False

    def test_invalid_email_no_domain(self):
        """Test email without domain."""
        is_valid, msg = validate_email("user@")
        assert is_valid is False

    def test_invalid_email_no_tld(self):
        """Test email without top-level domain."""
        is_valid, msg = validate_email("user@example")
        assert is_valid is False

    def test_empty_email(self):
        """Test empty email string."""
        is_valid, msg = validate_email("")
        assert is_valid is False

    def test_email_too_long(self):
        """Test email longer than 255 characters."""
        long_email = "a" * 250 + "@example.com"
        is_valid, msg = validate_email(long_email)
        assert is_valid is False


class TestValidateUsername:
    """Test cases for username validation."""

    def test_valid_username(self):
        """Test a valid username."""
        is_valid, msg = validate_username("validuser")
        assert is_valid is True
        assert msg == ""

    def test_valid_username_with_underscore(self):
        """Test username with underscore."""
        is_valid, msg = validate_username("valid_user_name")
        assert is_valid is True

    def test_valid_username_with_digits(self):
        """Test username with digits."""
        is_valid, msg = validate_username("user123")
        assert is_valid is True

    def test_username_too_short(self):
        """Test username shorter than 3 characters."""
        is_valid, msg = validate_username("ab")
        assert is_valid is False
        assert "at least 3 characters" in msg

    def test_username_too_long(self):
        """Test username longer than 50 characters."""
        long_username = "a" * 51
        is_valid, msg = validate_username(long_username)
        assert is_valid is False
        assert "exceed 50 characters" in msg

    def test_username_starts_with_digit(self):
        """Test that username starting with digit is rejected."""
        is_valid, msg = validate_username("1user")
        assert is_valid is False
        assert "start with a letter" in msg

    def test_username_with_special_chars(self):
        """Test that username with special characters is rejected."""
        is_valid, msg = validate_username("user@name")
        assert is_valid is False
        assert "alphanumeric" in msg

    def test_username_with_spaces(self):
        """Test that username with spaces is rejected."""
        is_valid, msg = validate_username("user name")
        assert is_valid is False

    def test_minimum_valid_username(self):
        """Test minimum valid username (3 characters)."""
        is_valid, msg = validate_username("abc")
        assert is_valid is True
