from functools import wraps
from flask import request, jsonify
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from .util import SECRET_KEY, ALGORITHM
import os


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        else:
            return jsonify({'message': 'Must be logged in to access'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_user_id = payload.get('sub')
        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user_id, *args, **kwargs)
    

    return decorated
