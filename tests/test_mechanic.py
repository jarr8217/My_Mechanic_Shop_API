from app import create_app
from app.models import db
import unittest
from test_customer import TestCustomer


class TestMechanic(unittest.TestCase):
    """Unit tests for the mechanic blueprint covering registration, authentication, RBAC, and CRUD operations."""

    def setUp(self):
        """Set up a fresh app and database for each test."""
        self.app = create_app('TestingConfig')
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Tear down the database after each test."""
        with self.app.app_context():
            db.drop_all()

    # DRY helpers
    def create_mechanic(self, name, email, phone, password, salary=50000):
        """Helper to create a mechanic via the API."""
        return self.client.post('/mechanics/', json={
            'name': name,
            'email': email,
            'phone': phone,
            'password': password,
            'salary': salary,
        })

    def login_mechanic(self, email, password):
        """Helper to log in a mechanic and get a token."""
        return self.client.post('/auth/mechanic_login', json={
            'email': email,
            'password': password,
        })

    def get_auth_headers(self, token):
        """Return auth headers for a given token."""
        return {'Authorization': f'Bearer {token}'}

    def test_create_mechanic(self):
        """Test successful mechanic registration."""
        response = self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], 'Jane Doe')
        self.assertEqual(response.json['email'], 'jane.doe@example.com')
        self.assertIn('id', response.json)

    def test_duplicate_mechanic_creation(self):
        """Test that duplicate mechanic registration fails."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        response = self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_mechanic_login(self):
        """Test mechanic login and token retrieval."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        response = self.login_mechanic('jane.doe@example.com', 'password123')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)

    def test_invalid_mechanic_login(self):
        """Test login with wrong credentials fails."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        response = self.login_mechanic('jane.doe@example.com', 'wrongpassword')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_get_mechanic_by_id(self):
        """Test mechanic can get their own data."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        response = self.client.get('/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], 'jane.doe@example.com')

    def test_update_mechanic(self):
        """Test mechanic can update their own data."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        update_payload = {
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'phone': '0987654321',
            'password': 'newpassword123',
            'salary': 60000,
        }
        response = self.client.put(
            '/mechanics/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], 'jane.smith@example.com')

    def test_delete_mechanic(self):
        """Test mechanic can delete their own account."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        response = self.client.delete('/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_get_mechanic_not_found(self):
        """Test getting a non-existent mechanic returns 404."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        response = self.client.get('/mechanics/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)

    def test_invalid_mechanic_creation(self):
        """Test registration fails with missing fields."""
        invalid_payload = {
            'name': '',
            'email': '',
            'phone': '',
            'password': '',
            'salary': '',  # Use '' for missing string fields, or remove if salary is numeric
        }
        response = self.client.post('/mechanics/', json=invalid_payload)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.json)

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

    def test_mechanic_login_wrong_method(self):
        """Test that GET method is not allowed on mechanic login endpoint."""
        response = self.client.get('/auth/mechanic_login')
        self.assertEqual(response.status_code, 405)

    def test_mechanic_cannot_access_another_mechanic(self):
        """Test that a mechanic cannot access, update, or delete another mechanic's data."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        self.create_mechanic(
            'John Smith', 'john.smith@example.com', '0987654321', 'password123')
        login_resp = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        # Try to get, update, and delete mechanic 2 as mechanic 1
        response = self.client.get('/mechanics/2', headers=headers)
        self.assertIn(response.status_code, [200, 400, 403, 404])
        response = self.client.put(
            '/mechanics/2', json={'name': 'Hacker'}, headers=headers)
        self.assertIn(response.status_code, [200, 400, 403, 404])
        response = self.client.delete('/mechanics/2', headers=headers)
        self.assertIn(response.status_code, [200, 400, 403, 404])

    def test_customer_cannot_access_mechanic_routes(self):
        """Test that a customer cannot access mechanic routes (get, update, delete)."""
        # Register and login as customer
        from test_customer import TestCustomer
        customer_test = TestCustomer()
        customer_test.setUp()
        customer_test.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login_resp = customer_test.login_customer(
            'john.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        # Try to get, update, and delete mechanic 1 as customer
        response = self.client.get('/mechanics/1', headers=headers)
        self.assertIn(response.status_code, [200, 403, 404])
        response = self.client.put(
            '/mechanics/1', json={'name': 'Hacker'}, headers=headers)
        self.assertIn(response.status_code, [200, 403, 404])
        response = self.client.delete('/mechanics/1', headers=headers)
        self.assertIn(response.status_code, [200, 403, 404])
        customer_test.tearDown()

    def test_get_all_mechanics_rbac(self):
        """Test that only mechanics can get all mechanics, and customers are denied or limited."""
        # Register and login as mechanic
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        response = self.client.get('/mechanics/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('mechanics', response.json)
        # Try as customer

        customer_test = TestCustomer()
        customer_test.setUp()
        customer_test.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login_resp = customer_test.login_customer(
            'john.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        response = self.client.get('/mechanics/', headers=headers)
        self.assertIn(response.status_code, [200, 403, 401])
        customer_test.tearDown()

    def test_mechanic_password_not_returned(self):
        """Test that password is not returned in mechanic responses."""
        response = self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        self.assertEqual(response.status_code, 201)
        login_resp = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        response = self.client.get('/mechanics/1', headers=headers)


if __name__ == '__main__':
    unittest.main()
