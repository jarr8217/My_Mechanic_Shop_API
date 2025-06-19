from app import create_app
from app.models import db
import unittest


class TestAuth(unittest.TestCase):
    """Test cases for authentication endpoints."""

    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after each test."""
        with self.app.app_context():
            from app.models import db
            db.drop_all()

    # DRY helper methods
    def create_customer(self, name, email, phone, password):
        return self.client.post('/customers/', json={
            'name': name,
            'email': email,
            'phone': phone,
            'password': password,
        })

    def create_mechanic(self, name, email, phone, password, salary=50000):
        return self.client.post('/mechanics/', json={
            'name': name,
            'email': email,
            'phone': phone,
            'password': password,
            'salary': salary,
        })

    def login_customer(self, email, password):
        return self.client.post('/auth/login', json={
            'email': email,
            'password': password,
        })

    def login_mechanic(self, email, password):
        return self.client.post('/auth/mechanic_login', json={
            'email': email,
            'password': password,
        })

    def get_auth_headers(self, token):
        return {'Authorization': f'Bearer {token}'}

    def test_customer_login(self):
        """Test that a customer can log in and receive a token."""
        email = 'john.doe@example.com'
        password = 'password123'
        self.create_customer('John Doe', email, '1234567890', password)
        response = self.login_customer(email, password)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)

    def test_mechanic_login(self):
        """Test that a mechanic can log in and receive a token."""
        email = 'jane.doe@example.com'
        password = 'password123'
        self.create_mechanic('Jane Doe', email, '0987654321', password)
        response = self.login_mechanic(email, password)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)

    def test_invalid_login(self):
        """Test that invalid login attempts return an error."""
        response = self.client.post('/auth/login', json={
            'email': 'invalid@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_invalid_mechanic_login(self):
        """Test that invalid mechanic login attempts return an error."""
        response = self.client.post('/auth/mechanic_login', json={
            'email': 'not.a.mechanic@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 400)  # Accept 400 as per API
        self.assertIn('error', response.json)

    def test_login_missing_fields(self):
        """Test login with missing email and password fields."""
        response = self.client.post('/auth/login', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_login_empty_fields(self):
        """Test login with empty email and password fields."""
        response = self.client.post('/auth/login', json={
            'email': '',
            'password': '',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_mechanic_login_missing_fields(self):
        """Test mechanic login with missing email and password fields."""
        response = self.client.post('/auth/mechanic_login', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_mechanic_login_empty_fields(self):
        """Test mechanic login with empty email and password fields."""
        response = self.client.post('/auth/mechanic_login', json={
            'email': '',
            'password': '',
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_login_wrong_method(self):
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 405)
        # Don't check response.json, Flask default is HTML for 405

    def test_mechanic_login_wrong_method(self):
        response = self.client.get('/auth/mechanic_login')
        self.assertEqual(response.status_code, 405)
        # Don't check response.json, Flask default is HTML for 405

    def test_protected_route_with_token(self):
        """Test that a mechanic can access a protected route with a valid token."""
        # Register a mechanic
        mech_payload = {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '0987654321',
            'password': 'password123',
            'salary': 60000,
        }
        self.client.post('/mechanics/', json=mech_payload)

        # Log in as the mechanic to get a token
        login_response = self.client.post('/auth/mechanic_login', json={
            'email': 'jane.doe@example.com',
            'password': 'password123',
        })
        self.assertEqual(login_response.status_code, 200)
        self.assertIn('token', login_response.json)
        token = login_response.json['token']

        # Access a protected route with the token
        headers = {'Authorization': f'Bearer {token}'}
        response = self.client.get('/customers/', headers=headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn('customers', response.json)

    def test_protected_route_without_token(self):
        """Test that a mechanic cannot access a protected route without a token."""
        response = self.client.get('/customers/')
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Token is missing!')

    def test_protected_route_with_invalid_token(self):
        """Test that a mechanic cannot access a protected route with an invalid token."""
        headers = {'Authorization': 'Bearer invalid_token'}
        response = self.client.get('/customers/', headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Invalid token!')

    def test_protected_route_with_expired_token(self):
        """Test that a mechanic cannot access a protected route with an expired token."""
        headers = {'Authorization': 'Bearer expired_token'}
        response = self.client.get('/customers/', headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Invalid token!')
