import unittest
from app import create_app
from app.models import db


class TestInventory(unittest.TestCase):
    def setUp(self):
        """Set up test variables and client."""
        self.app = create_app('TestingConfig')
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Tear down test variables."""
        with self.app.app_context():
            db.drop_all()

    # DRY helpers
    def create_mechanic(self, name, email, phone, password, salary=50000):
        return self.client.post('/mechanics/', json={
            'name': name,
            'email': email,
            'phone': phone,
            'password': password,
            'salary': salary,
        })

    def login_mechanic(self, email, password):
        return self.client.post('/auth/mechanic_login', json={
            'email': email,
            'password': password,
        })

    def get_auth_headers(self, token):
        return {'Authorization': f'Bearer {token}'}

    def create_inventory(self, token, part_name, part_number, quantity, price):
        headers = self.get_auth_headers(token)
        return self.client.post('/inventory/', json={
            'part_name': part_name,
            'part_number': part_number,
            'quantity': quantity,
            'price': price,
        }, headers=headers)

    def test_create_inventory_mechanic(self):
        """Test that a mechanic can create an inventory item."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        login = self.login_mechanic('jane.doe@example.com', 'password123')
        token = login.json['token']
        resp = self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json['part_name'], 'Brake Pad')
        self.assertEqual(resp.json['part_number'], 'BP-001')
        self.assertEqual(resp.json['quantity'], 10)
        self.assertEqual(resp.json['price'], 49.99)

    def test_create_inventory_duplicate(self):
        """Test that duplicate part_number fails."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        resp = self.create_inventory(token, 'Brake Pad 2', 'BP-001', 5, 59.99)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.json)

    def test_create_inventory_missing_fields(self):
        """Test that missing fields returns 400."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        headers = self.get_auth_headers(token)
        resp = self.client.post(
            '/inventory/', json={'part_name': 'Brake Pad'}, headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_create_inventory_customer_forbidden(self):
        """Test that a customer cannot create inventory item."""
        from test_customer import TestCustomer
        cust = TestCustomer()
        cust.setUp()
        cust.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login = cust.login_customer('john.doe@example.com', 'password123')
        token = login.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        resp = self.client.post('/inventory/', json={
            'part_name': 'Brake Pad', 'part_number': 'BP-002', 'quantity': 5, 'price': 19.99
        }, headers=headers)
        self.assertIn(resp.status_code, [401, 403])
        cust.tearDown()

    def test_create_inventory_unauthenticated(self):
        """Test that unauthenticated user cannot create inventory item."""
        resp = self.client.post('/inventory/', json={
            'part_name': 'Brake Pad', 'part_number': 'BP-003', 'quantity': 5, 'price': 19.99
        })
        self.assertIn(resp.status_code, [401, 403])

    def test_get_all_inventory(self):
        """Test that anyone can get all inventory items (pagination)."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        self.create_inventory(token, 'Rotor', 'RT-001', 5, 99.99)
        resp = self.client.get('/inventory/?page=1&limit=2')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('inventory_items', resp.json)
        self.assertEqual(resp.json['page'], 1)
        self.assertEqual(resp.json['per_page'], 2)
        self.assertGreaterEqual(resp.json['total'], 2)

    def test_get_inventory_by_id(self):
        """Test that anyone can get inventory item by ID."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        resp = self.client.get('/inventory/1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['part_name'], 'Brake Pad')

    def test_get_inventory_by_id_not_found(self):
        """Test that 404 is returned if inventory item not found."""
        resp = self.client.get('/inventory/999')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_update_inventory_mechanic(self):
        """Test that a mechanic can update inventory item."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        headers = self.get_auth_headers(token)
        resp = self.client.put('/inventory/1', json={
            'part_name': 'Brake Pad Updated',
            'part_number': 'BP-001',
            'quantity': 20,
            'price': 59.99
        }, headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['part_name'], 'Brake Pad Updated')
        self.assertEqual(resp.json['quantity'], 20)

    def test_update_inventory_not_found(self):
        """Test that 404 is returned if updating non-existent inventory item."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        headers = self.get_auth_headers(token)
        resp = self.client.put('/inventory/999', json={
            'part_name': 'Brake Pad',
            'part_number': 'BP-999',
            'quantity': 1,
            'price': 1.0
        }, headers=headers)
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_update_inventory_customer_forbidden(self):
        """Test that a customer cannot update inventory item."""
        from test_customer import TestCustomer
        cust = TestCustomer()
        cust.setUp()
        cust.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login = cust.login_customer('john.doe@example.com', 'password123')
        token = login.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        resp = self.client.put('/inventory/1', json={
            'part_name': 'Brake Pad', 'part_number': 'BP-001', 'quantity': 1, 'price': 1.0
        }, headers=headers)
        self.assertIn(resp.status_code, [401, 403, 404])
        cust.tearDown()

    def test_partial_update_inventory(self):
        """Test that a mechanic can partially update inventory item."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        headers = self.get_auth_headers(token)
        resp = self.client.patch(
            '/inventory/1', json={'quantity': 99}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['quantity'], 99)

    def test_partial_update_inventory_not_found(self):
        """Test that 404 is returned if partially updating non-existent inventory item."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        headers = self.get_auth_headers(token)
        resp = self.client.patch(
            '/inventory/999', json={'quantity': 99}, headers=headers)
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_delete_inventory_mechanic(self):
        """Test that a mechanic can delete inventory item."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        headers = self.get_auth_headers(token)
        resp = self.client.delete('/inventory/1', headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('message', resp.json)

    def test_delete_inventory_not_found(self):
        """Test that 404 is returned if deleting non-existent inventory item."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        headers = self.get_auth_headers(token)
        resp = self.client.delete('/inventory/999', headers=headers)
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_delete_inventory_customer_forbidden(self):
        """Test that a customer cannot delete inventory item."""
        from test_customer import TestCustomer
        cust = TestCustomer()
        cust.setUp()
        cust.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login = cust.login_customer('john.doe@example.com', 'password123')
        token = login.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        resp = self.client.delete('/inventory/1', headers=headers)
        self.assertIn(resp.status_code, [401, 403, 404])
        cust.tearDown()

    def test_delete_inventory_unauthenticated(self):
        """Test that unauthenticated user cannot delete inventory item."""
        resp = self.client.delete('/inventory/1')
        self.assertIn(resp.status_code, [401, 403, 404])

    def test_inventory_password_not_returned(self):
        """Test that password is never in inventory responses."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        resp = self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        self.assertNotIn('password', resp.json)
        get_resp = self.client.get('/inventory/1')
        self.assertNotIn('password', get_resp.json)

    def test_create_inventory_invalid_types(self):
        """Test that invalid data types for quantity/price returns 400."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        headers = self.get_auth_headers(token)
        resp = self.client.post('/inventory/', json={
            'part_name': 'Brake Pad', 'part_number': 'BP-004', 'quantity': 'ten', 'price': 49.99
        }, headers=headers)
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post('/inventory/', json={
            'part_name': 'Rotor', 'part_number': 'RT-004', 'quantity': 5, 'price': 'expensive'
        }, headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_create_inventory_negative_values(self):
        """Test that negative quantity/price returns 400."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        headers = self.get_auth_headers(token)
        resp = self.client.post('/inventory/', json={
            'part_name': 'Rotor', 'part_number': 'RT-NEG', 'quantity': -5, 'price': 99.99
        }, headers=headers)
        self.assertEqual(resp.status_code, 400)
        resp = self.client.post('/inventory/', json={
            'part_name': 'Rotor', 'part_number': 'RT-NEG2', 'quantity': 5, 'price': -99.99
        }, headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_patch_empty_payload(self):
        """Test that PATCH with empty payload returns 400."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        headers = self.get_auth_headers(token)
        resp = self.client.patch('/inventory/1', json={}, headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_patch_invalid_field(self):
        """Test that PATCH with invalid field returns 400."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        headers = self.get_auth_headers(token)
        resp = self.client.patch(
            '/inventory/1', json={'not_a_field': 123}, headers=headers)
        self.assertEqual(resp.status_code, 400)

    def test_wrong_methods(self):
        """Test that wrong HTTP methods return 405 or 404."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        headers = self.get_auth_headers(token)
        resp = self.client.post('/inventory/1', headers=headers)
        self.assertIn(resp.status_code, [404, 405])
        resp = self.client.put('/inventory/', headers=headers)
        self.assertIn(resp.status_code, [404, 405])
        resp = self.client.patch('/inventory/', headers=headers)
        self.assertIn(resp.status_code, [404, 405])
        resp = self.client.delete('/inventory/', headers=headers)
        self.assertIn(resp.status_code, [404, 405])

    def test_get_all_inventory_response_keys(self):
        """Test that all expected keys are present in get all inventory response."""
        self.create_mechanic(
            'Jane Doe', 'jane.doe@example.com', '1234567890', 'password123')
        token = self.login_mechanic(
            'jane.doe@example.com', 'password123').json['token']
        self.create_inventory(token, 'Brake Pad', 'BP-001', 10, 49.99)
        resp = self.client.get('/inventory/?page=1&limit=1')
        self.assertEqual(resp.status_code, 200)
        for key in ['inventory_items', 'page', 'per_page', 'total', 'pages']:
            self.assertIn(key, resp.json)

    def test_rbac_error_messages(self):
        """Test that customer/unauthenticated RBAC error messages are consistent."""
        from test_customer import TestCustomer
        cust = TestCustomer()
        cust.setUp()
        cust.create_customer(
            'John Doe', 'john.doe@example.com', '1234567890', 'password123')
        login = cust.login_customer('john.doe@example.com', 'password123')
        token = login.json['token']
        headers = {'Authorization': f'Bearer {token}'}
        resp = self.client.post('/inventory/', json={
            'part_name': 'Brake Pad', 'part_number': 'BP-002', 'quantity': 5, 'price': 19.99
        }, headers=headers)
        self.assertIn(resp.status_code, [401, 403])
        if resp.status_code in [401, 403]:
            self.assertTrue('error' in resp.json or 'message' in resp.json)
        cust.tearDown()
        resp = self.client.post('/inventory/', json={
            'part_name': 'Brake Pad', 'part_number': 'BP-003', 'quantity': 5, 'price': 19.99
        })
        self.assertIn(resp.status_code, [401, 403])
        if resp.status_code in [401, 403]:
            self.assertTrue('error' in resp.json or 'message' in resp.json)


if __name__ == '__main__':
    unittest.main()
