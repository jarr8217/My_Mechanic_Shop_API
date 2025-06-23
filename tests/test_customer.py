from app import create_app
from app.models import db
import unittest


class TestCustomer(unittest.TestCase):

    def setUp(self):
        self.app = create_app('TestingConfig')
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
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

    def test_create_customer(self):
        """Test successful customer registration."""
        response = self.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], 'John Doe')
        self.assertEqual(response.json['email'], 'john.doe@example.com')
        self.assertEqual(response.json['phone'], '1234567890')
        self.assertIn('id', response.json)

    def test_invalid_creation(self):
        """Test registration fails with missing fields."""
        invalid_payload = {
            'name': '',
            'email': '',
            'phone': '',
            'password': '',
        }

        response = self.client.post('/customers/', json=invalid_payload)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.json)

    def test_duplicate_customer_creation(self):
        """Test that duplicate customer registration fails."""
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)
        response = self.client.post('/customers/', json=cust_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_get_all_customers(self):
        """Test that mechanic can retrieve all customers."""
        # Register a mechanic
        mech_payload = {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '0987654321',
            'password': 'password123',
            'salary': 50000,
        }
        self.client.post('/mechanics/', json=mech_payload)

        # Register a customer
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)

        # Log in as mechanic
        login_resp = self.client.post('/auth/mechanic_login', json={
            'email': 'jane.doe@example.com',
            'password': 'password123',
        })
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}

        # Get all customers
        response = self.client.get('/customers/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('customers', response.json)
        self.assertGreaterEqual(len(response.json['customers']), 1)

    def test_get_customer_by_id(self):
        """Test that a customer can retrieve their own data."""
        self.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_customer('john.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        response = self.client.get('/customers/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], 'john.doe@example.com')

    def test_update_customer(self):
        """Test that a customer can update their own data."""
        self.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_customer('john.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        update_payload = {
            'name': 'John Smith',
            'email': 'john.smith@example.com',
            'phone': '0987654321',
            'password': 'newpassword123',
        }
        response = self.client.put(
            '/customers/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], 'john.smith@example.com')

    def test_partial_update_customer(self):
        """Test that a customer can partially update their own data."""
        self.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login_resp = self.login_customer('john.doe@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        partial_update_payload = {'name': 'John Smith'}
        response = self.client.patch(
            '/customers/1', json=partial_update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], 'John Smith')

    def test_delete_customer(self):
        """Test that a customer can delete their own account."""
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)

        # Log in as the customer
        login_resp = self.client.post('/auth/login', json={
            'email': 'john.doe@example.com',
            'password': 'password123',
        })
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}

        # Delete customer account
        response = self.client.delete('/customers/1', headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_get_customers_by_search(self):
        """Test that customers can be searched by name or email by mechanics."""
        # Register a mechanic
        mech_payload = {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'salary': 50000,
        }
        self.client.post('/mechanics/', json=mech_payload)
        # Log in as the mechanic
        login_resp = self.client.post('/auth/mechanic_login', json={
            'email': 'jane.doe@example.com',
            'password': 'password123',
        })
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}

        # Create two customers
        cust_payload1 = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload1)

        cust_payload2 = {
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'phone': '0987654321',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload2)

        # Search customers by name
        response = self.client.get(
            '/customers/search', query_string={'name': 'John'}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['email'], 'john.doe@example.com')

        # Search customers by email
        response = self.client.get(
            '/customers/search', query_string={'email': 'jane.smith@example.com'}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['name'], 'Jane Smith')

    def test_get_customers_by_search_no_results(self):
        """Test that searching for a non-existent customer returns an empty list."""
        # Register a mechanic
        mech_payload = {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
            'salary': 50000,
        }
        self.client.post('/mechanics/', json=mech_payload)
        # Log in as the mechanic
        login_resp = self.client.post('/auth/mechanic_login', json={
            'email': 'jane.doe@example.com',
            'password': 'password123',
        })
        self.assertEqual(login_resp.status_code, 200)
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}

        # Search for a non-existent customer by name
        response = self.client.get(
            '/customers/search', query_string={'name': 'NonExistent'}, headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'],
                         'No customers found matching the criteria')

    def test_get_customers_by_search_unauthorized(self):
        """Test that unauthorized access to search customers returns 401."""
        response = self.client.get(
            '/customers/search', query_string={'name': 'John'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Token is missing!')

    def test_login_with_uppercase_email(self):
        self.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        response = self.login_customer('JOHN.DOE@EXAMPLE.COM', 'password123')
        self.assertEqual(response.status_code, 400)

    def test_update_customer_unauthorized(self):
        """Test that a customer cannot update another customer's data."""
        self.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        self.create_customer(
            'Jane Smith', 'jane.smith@example.com', '0987654321', 'password123')
        login_resp = self.login_customer(
            'jane.smith@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        update_payload = {'name': 'Hacker'}
        response = self.client.put(
            '/customers/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', response.json)

    def test_delete_customer_unauthorized(self):
        """Test that a customer cannot delete another customer's account."""
        self.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        self.create_customer(
            'Jane Smith', 'jane.smith@example.com', '0987654321', 'password123')
        login_resp = self.login_customer(
            'jane.smith@example.com', 'password123')
        token = login_resp.json['token']
        headers = self.get_auth_headers(token)
        response = self.client.delete('/customers/1', headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn('error', response.json)

    def test_mechanic_cannot_update_customer(self):
        """Test that a mechanic cannot update a customer's data."""
        # Register mechanic
        mech_payload = {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '0987654321',
            'password': 'password123',
            'salary': 50000,
        }
        self.client.post('/mechanics/', json=mech_payload)
        # Register customer
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)
        # Log in as mechanic
        login_resp = self.client.post('/auth/mechanic_login', json={
            'email': 'jane.doe@example.com',
            'password': 'password123',
        })
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        # Try to update customer
        update_payload = {'name': 'Hacker'}
        response = self.client.put(
            '/customers/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn('message', response.json)

    def test_mechanic_cannot_delete_customer(self):
        """Test that a mechanic cannot delete a customer's account."""
        # Register mechanic
        mech_payload = {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '0987654321',
            'password': 'password123',
            'salary': 50000,
        }
        self.client.post('/mechanics/', json=mech_payload)
        # Register customer
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)
        # Log in as mechanic
        login_resp = self.client.post('/auth/mechanic_login', json={
            'email': 'jane.doe@example.com',
            'password': 'password123',
        })
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        # Try to delete customer
        response = self.client.delete('/customers/1', headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn('message', response.json)

    def test_get_customer_not_found(self):
        """Test getting a non-existent customer returns 404."""
        # Register and login as mechanic
        mech_payload = {
            'name': 'Jane Doe',
            'email': 'jane.doe@example.com',
            'phone': '0987654321',
            'password': 'password123',
            'salary': 50000,
        }
        self.client.post('/mechanics/', json=mech_payload)
        login_resp = self.client.post('/auth/mechanic_login', json={
            'email': 'jane.doe@example.com',
            'password': 'password123',
        })
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        # Try to get a non-existent customer
        response = self.client.get('/customers/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Customer not found')

    def test_update_customer_not_found(self):
        """Test updating a non-existent customer returns 404."""
        # Register and login as customer
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)
        login_resp = self.client.post('/auth/login', json={
            'email': 'john.doe@example.com',
            'password': 'password123',
        })
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        # Try to update a non-existent customer
        response = self.client.put(
            '/customers/999', json={'name': 'Ghost'}, headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)

    def test_partial_update_customer_not_found(self):
        """Test partially updating a non-existent customer returns 404."""
        # Register and login as customer
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)
        login_resp = self.client.post('/auth/login', json={
            'email': 'john.doe@example.com',
            'password': 'password123',
        })
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        # Try to partially update a non-existent customer
        response = self.client.patch(
            '/customers/999', json={'name': 'Ghost'}, headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)

    def test_delete_customer_not_found(self):
        """Test deleting a non-existent customer returns 404."""
        # Register and login as customer
        cust_payload = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'password': 'password123',
        }
        self.client.post('/customers/', json=cust_payload)
        login_resp = self.client.post('/auth/login', json={
            'email': 'john.doe@example.com',
            'password': 'password123',
        })
        token = login_resp.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        # Try to delete a non-existent customer
        response = self.client.delete('/customers/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json)
        self.assertEqual(response.json['error'], 'Customer not found')


if __name__ == '__main__':
    unittest.main()
