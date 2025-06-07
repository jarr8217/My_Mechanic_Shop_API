from functools import wraps
from flask import request, jsonify
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from .util import SECRET_KEY, ALGORITHM


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
            current_user_id = int(payload.get('sub'))
            current_user_role = payload.get('role')
        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user_id, *args, current_user_role=current_user_role, **kwargs)
    return decorated

def mechanic_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        else:
            return jsonify({'error': 'Token is missing!'}), 401
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_user_id = int(payload.get('sub'))
            current_user_role = payload.get('role')
            if current_user_role != 'mechanic':
                return jsonify({'error': 'Mechanic access required!'}), 403
        except ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401
        return f(current_user_id, current_user_role, *args, **kwargs)
    return decorated

def customer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        else:
            return jsonify({'message': 'Must be logged in as a customer to access'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            current_user_id = int(payload.get('sub'))
            current_user_role = payload.get('role')
            if current_user_role != 'customer':
                return jsonify({'message': 'Customer access required'}), 403
        except ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(current_user_id, *args, current_user_role=current_user_role, **kwargs)

    return decorated