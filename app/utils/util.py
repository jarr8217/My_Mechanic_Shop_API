"""Utility functions for token encoding/decoding and other helpers."""
from datetime import datetime, timedelta, timezone
import jwt
import os


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'


def encode_token(customer_id):
    """Encode a JWT token for a customer.

    Args:
        customer_id: The ID of the customer.

    Returns:
        str: The encoded JWT token.
    """
    payload = {
        # exp hour from now
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),  # the time is issued
        'sub': str(customer_id),  # subject
        'role': 'customer'  # role of the user
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def encode_mechanic_token(mechanic_id):
    """Encode a JWT token for a mechanic.

    Args:
        mechanic_id: The ID of the mechanic.

    Returns:
        str: The encoded JWT token.
    """
    payload = {
        # exp hour from now
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),  # the time is issued
        'sub': str(mechanic_id),  # subject
        'role': 'mechanic'  # role of the user
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
