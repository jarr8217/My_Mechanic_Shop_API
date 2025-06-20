import unittest
from app import create_app
from app.models import db
from datetime import date


class TestServiceTicket(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    # DRY helpers
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

    def create_inventory(self, part_name, part_number, quantity, price, token):
        headers = self.get_auth_headers(token)
        return self.client.post('/inventory/', json={
            'part_name': part_name,
            'part_number': part_number,
            'quantity': quantity,
            'price': price,
        }, headers=headers)

    def create_ticket(self, token, customer_id, vin='VIN123456', service_date='2025-01-01', desc='Oil change'):
        headers = self.get_auth_headers(token)
        return self.client.post('/service_tickets/', json={
            'VIN': vin,
            'service_date': service_date,
            'service_desc': desc,
            'customer_id': customer_id
        }, headers=headers)

    # --- TESTS ---
    def test_create_service_ticket_success(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        cust_login = self.login_customer('alice@example.com', 'pw123')
        mech_token = mech_login.json['token']
        cust_id = 1
        resp = self.create_ticket(
            mech_token, cust_id, vin='VIN0001', service_date='2025-05-01', desc='Brake job')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json['VIN'], 'VIN0001')
        self.assertEqual(resp.json['customer_id'], cust_id)
        self.assertEqual(resp.json['service_desc'], 'Brake job')
        self.assertIn('id', resp.json)

    def test_create_service_ticket_duplicate_vin(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VIN0002')
        resp = self.create_ticket(mech_token, cust_id, vin='VIN0002')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.json)

    def test_create_service_ticket_missing_fields(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        # Missing VIN
        resp = self.client.post('/service_tickets/', json={
            'service_date': '2025-01-01',
            'service_desc': 'Missing VIN',
            'customer_id': 1
        }, headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 400)
        # Missing customer_id
        resp2 = self.client.post('/service_tickets/', json={
            'VIN': 'VIN0003',
            'service_date': '2025-01-01',
            'service_desc': 'Missing customer',
        }, headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp2.status_code, 400)

    def test_create_service_ticket_forbidden_for_customer(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        cust_login = self.login_customer('alice@example.com', 'pw123')
        cust_token = cust_login.json['token']
        resp = self.client.post('/service_tickets/', json={
            'VIN': 'VIN0004',
            'service_date': '2025-01-01',
            'service_desc': 'Should fail',
            'customer_id': 1
        }, headers=self.get_auth_headers(cust_token))
        self.assertEqual(resp.status_code, 403)

    def test_get_all_service_tickets_pagination(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        cust_id = 1
        # Create 3 tickets
        for i in range(3):
            self.create_ticket(mech_token, cust_id,
                               vin=f'VINPG{i}', service_date=f'2025-01-0{i+1}')
        resp = self.client.get(
            '/service_tickets/?page=1&limit=2', headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('service_tickets', resp.json)
        self.assertEqual(len(resp.json['service_tickets']), 2)
        self.assertEqual(resp.json['page'], 1)
        self.assertEqual(resp.json['total'], 3)
        self.assertGreaterEqual(resp.json['pages'], 2)

    def test_get_all_service_tickets_forbidden_for_customer(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        cust_login = self.login_customer('alice@example.com', 'pw123')
        cust_token = cust_login.json['token']
        resp = self.client.get('/service_tickets/',
                               headers=self.get_auth_headers(cust_token))
        self.assertEqual(resp.status_code, 403)

    def test_get_service_ticket_by_id_mechanic_and_customer(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        cust_login = self.login_customer('alice@example.com', 'pw123')
        mech_token = mech_login.json['token']
        cust_token = cust_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VINGET1')
        # Mechanic can get
        resp = self.client.get('/service_tickets/1',
                               headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json['VIN'], 'VINGET1')
        # Customer can get their own
        resp2 = self.client.get('/service_tickets/1',
                                headers=self.get_auth_headers(cust_token))
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json['VIN'], 'VINGET1')

    def test_get_service_ticket_by_id_unauthorized(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VINGET2')
        # No token
        resp = self.client.get('/service_tickets/1')
        self.assertEqual(resp.status_code, 401)
        self.assertIn('message', resp.json)

    def test_get_service_ticket_by_id_not_found(self):
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        resp = self.client.get('/service_tickets/999',
                               headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_edit_service_ticket_add_remove_mechanic(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        self.create_mechanic('Carl', 'carl@example.com', '3334445555', 'pw789')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        carl_login = self.login_mechanic('carl@example.com', 'pw789')
        mech_token = mech_login.json['token']
        carl_id = 2
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VINEDIT1')

        edit_payload = {'add_mechanic_ids': [
            carl_id], 'remove_mechanic_ids': []}
        resp = self.client.put('/service_tickets/edit/1', json=edit_payload,
                               headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('mechanics', resp.json)
        self.assertTrue(
            any(m['id'] == carl_id for m in resp.json['mechanics']))
        # Remove Carl
        edit_payload2 = {'add_mechanic_ids': [],
                         'remove_mechanic_ids': [carl_id]}
        resp2 = self.client.put(
            '/service_tickets/edit/1', json=edit_payload2, headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp2.status_code, 200)
        self.assertTrue(
            all(m['id'] != carl_id for m in resp2.json['mechanics']))

    def test_edit_service_ticket_mechanic_not_found(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VINEDIT2')
        # Try to add non-existent mechanic
        edit_payload = {'add_mechanic_ids': [999], 'remove_mechanic_ids': []}
        resp = self.client.put('/service_tickets/edit/1', json=edit_payload,
                               headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_edit_service_ticket_not_found(self):
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        edit_payload = {'add_mechanic_ids': [1], 'remove_mechanic_ids': []}
        resp = self.client.put('/service_tickets/edit/999',
                               json=edit_payload, headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_add_remove_inventory_part(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VINPART1')
        # Add inventory part
        inv_resp = self.create_inventory(
            'Brake Pad', 'BP-001', 10, 50.0, mech_token)
        part_id = inv_resp.json['id']
        add_part_payload = {'quantity': 2}
        resp = self.client.put(
            f'/service_tickets/1/add_part/{part_id}', json=add_part_payload, headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('message', resp.json)
        # Remove part
        resp2 = self.client.delete(
            f'/service_tickets/1/remove_part/{part_id}', headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp2.status_code, 200)
        self.assertIn('message', resp2.json)

    def test_add_inventory_part_invalid(self):
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        # No such ticket or part
        add_part_payload = {'quantity': 2}
        resp = self.client.put('/service_tickets/999/add_part/999',
                               json=add_part_payload, headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)
        # Invalid quantity
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_ticket(mech_token, 1, vin='VINPART2')
        inv_resp = self.create_inventory(
            'Rotor', 'RT-001', 10, 80.0, mech_token)
        part_id = inv_resp.json['id']
        bad_payload = {'quantity': 0}
        resp2 = self.client.put(
            f'/service_tickets/1/add_part/{part_id}', json=bad_payload, headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp2.status_code, 400)
        self.assertIn('error', resp2.json)

    def test_remove_inventory_part_not_found(self):
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        resp = self.client.delete(
            '/service_tickets/1/remove_part/999', headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 404)
        self.assertIn('error', resp.json)

    def test_list_ticket_parts(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        cust_login = self.login_customer('alice@example.com', 'pw123')
        mech_token = mech_login.json['token']
        cust_token = cust_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VINPARTS1')
        inv_resp = self.create_inventory(
            'Filter', 'FLT-001', 5, 20.0, mech_token)
        part_id = inv_resp.json['id']
        self.client.put(f'/service_tickets/1/add_part/{part_id}', json={
                        'quantity': 1}, headers=self.get_auth_headers(mech_token))
        resp = self.client.get('/service_tickets1/parts',
                               headers=self.get_auth_headers(mech_token))
        self.assertIn(resp.status_code, (200, 404))
        resp2 = self.client.get('/service_tickets1/parts',
                                headers=self.get_auth_headers(cust_token))
        self.assertIn(resp2.status_code, (200, 404))

    def test_list_ticket_parts_unauthorized(self):
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_ticket(mech_token, 1, vin='VINPARTS2')
        # Unrelated customer
        self.create_customer('Eve', 'eve@example.com', '4445556666', 'pw999')
        eve_login = self.login_customer('eve@example.com', 'pw999')
        eve_token = eve_login.json['token']
        resp = self.client.get('/service_tickets1/parts',
                               headers=self.get_auth_headers(eve_token))
        self.assertIn(resp.status_code, (403, 404))

    def test_customer_my_tickets(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        cust_login = self.login_customer('alice@example.com', 'pw123')
        mech_token = mech_login.json['token']
        cust_token = cust_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id, vin='VINMYT1')
        resp = self.client.get('/service_tickets/my-tickets',
                               headers=self.get_auth_headers(cust_token))
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertGreaterEqual(len(resp.json), 1)

    def test_customer_my_tickets_none(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        cust_login = self.login_customer('alice@example.com', 'pw123')
        cust_token = cust_login.json['token']
        resp = self.client.get('/service_tickets/my-tickets',
                               headers=self.get_auth_headers(cust_token))
        self.assertEqual(resp.status_code, 404)
        self.assertIn('message', resp.json)

    def test_search_service_tickets_by_vin_and_date(self):
        self.create_customer('Alice', 'alice@example.com',
                             '1112223333', 'pw123')
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        cust_id = 1
        self.create_ticket(mech_token, cust_id,
                           vin='VINSEARCH1', service_date='2025-06-01')
        # Search by VIN
        resp = self.client.get(
            '/service_tickets/search?vin=VINSEARCH1', headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json, list)
        self.assertGreaterEqual(len(resp.json), 1)
        # Search by date
        resp2 = self.client.get(
            '/service_tickets/search?service_date=2025-06-01', headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp2.status_code, 200)
        self.assertIsInstance(resp2.json, list)
        self.assertGreaterEqual(len(resp2.json), 1)

    def test_search_service_tickets_invalid_date(self):
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        resp = self.client.get('/service_tickets/search?start_date=bad-date&end_date=bad-date',
                               headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('error', resp.json)

    def test_search_service_tickets_not_found(self):
        self.create_mechanic('Bob', 'bob@example.com', '2223334444', 'pw456')
        mech_login = self.login_mechanic('bob@example.com', 'pw456')
        mech_token = mech_login.json['token']
        resp = self.client.get(
            '/service_tickets/search?vin=NOTFOUND', headers=self.get_auth_headers(mech_token))
        self.assertEqual(resp.status_code, 404)
        self.assertIn('message', resp.json)


if __name__ == '__main__':
    unittest.main()
