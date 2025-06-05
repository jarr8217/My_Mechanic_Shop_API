from datetime import datetime, timedelta, timezone
import jwt
import os


SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = 'HS256'

def encode_token(customer_id):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(hours=1), # exp hour from now
        'iat': datetime.now(timezone.utc), # the time is issued
        'sub': str(customer_id), # subject
        'role': 'customer' # role of the user
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def encode_mechanic_token(mechanic_id):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),  # exp hour from now
        'iat': datetime.now(timezone.utc),  # the time is issued
        'sub': str(mechanic_id),  # subject
        'role': 'mechanic'  # role of the user
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
