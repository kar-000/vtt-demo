"""Unit tests for JWT token handling."""

from datetime import timedelta

import pytest
from app.core.config import settings
from app.core.security import create_access_token, decode_access_token
from jose import JWTError, jwt


def test_create_token_with_string_sub():
    """Test that tokens are created with 'sub' as a string."""
    user_id = 123
    token = create_access_token(data={"sub": str(user_id)})

    # Manually decode to verify structure
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    # Verify 'sub' is a string, not an integer
    assert isinstance(payload["sub"], str)
    assert payload["sub"] == "123"
    assert "exp" in payload


def test_token_roundtrip():
    """Test encoding and decoding a token."""
    user_id = 42
    original_data = {"sub": str(user_id)}

    # Create token
    token = create_access_token(data=original_data)

    # Decode token
    decoded = decode_access_token(token)

    # Verify data survived roundtrip
    assert decoded is not None
    assert decoded["sub"] == str(user_id)
    assert isinstance(decoded["sub"], str)


def test_token_with_custom_expiry():
    """Test creating a token with custom expiration time."""
    user_id = 99
    expires_delta = timedelta(minutes=30)

    token = create_access_token(data={"sub": str(user_id)}, expires_delta=expires_delta)
    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "99"
    assert "exp" in decoded


def test_decode_invalid_token():
    """Test that invalid tokens return None."""
    invalid_token = "invalid.token.here"

    result = decode_access_token(invalid_token)

    assert result is None


def test_decode_token_wrong_secret():
    """Test that tokens signed with wrong secret are rejected."""
    user_id = 123

    # Create token with wrong secret
    wrong_token = jwt.encode({"sub": str(user_id), "exp": 9999999999}, "wrong-secret-key", algorithm=settings.ALGORITHM)

    # Try to decode with correct secret
    result = decode_access_token(wrong_token)

    assert result is None


def test_decode_token_wrong_algorithm():
    """Test that tokens with wrong algorithm are rejected."""
    user_id = 123

    # Create token with different algorithm
    wrong_algo_token = jwt.encode(
        {"sub": str(user_id), "exp": 9999999999}, settings.SECRET_KEY, algorithm="HS512"  # Different from HS256
    )

    # Try to decode
    result = decode_access_token(wrong_algo_token)

    assert result is None


def test_token_with_integer_sub_fails():
    """
    Test that tokens with integer 'sub' claim fail JWT validation.
    This is a regression test for the bug where we passed integer user IDs.
    """
    user_id = 123

    # Try to create a token with integer sub (should fail JWT validation)
    with pytest.raises(JWTError):
        # Manually encode with integer sub to test the failure
        token = jwt.encode(
            {"sub": user_id, "exp": 9999999999}, settings.SECRET_KEY, algorithm=settings.ALGORITHM  # Integer sub
        )
        # JWT encoding succeeds, but decoding should fail
        jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def test_token_preserves_string_format():
    """Test that 'sub' claim preserves string format through encode/decode."""
    test_cases = ["1", "123", "999"]

    for user_id_str in test_cases:
        token = create_access_token(data={"sub": user_id_str})
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == user_id_str
        assert isinstance(decoded["sub"], str)


def test_decode_expired_token():
    """Test that expired tokens are rejected."""
    user_id = 123

    # Create token that expired immediately
    token = create_access_token(data={"sub": str(user_id)}, expires_delta=timedelta(seconds=-1))  # Already expired

    result = decode_access_token(token)

    # Should return None for expired tokens
    assert result is None
