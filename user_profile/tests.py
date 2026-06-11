from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from user_profile.models import Address

User = get_user_model()

class AddressAjaxTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.login(username='testuser@example.com', password='testpassword')

    def test_add_address_ajax_success(self):
        response = self.client.post(
            reverse('user_profile:add_address_ajax'),
            {
                'full_name': 'John Doe',
                'phone': '1234567890',
                'address': '123 Main Street',
                'city': 'Metropolis',
                'district': 'District 1',
                'state': 'New York',
                'pincode': '10001',
                'landmark': 'Near Park',
                'is_default': 'on'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['address']['full_name'], 'John Doe')
        self.assertEqual(data['address']['pincode'], '10001')
        self.assertTrue(data['address']['is_default'])

        # Verify it was saved in DB
        self.assertTrue(Address.objects.filter(user=self.user, pincode='10001').exists())

    def test_add_address_ajax_missing_fields(self):
        response = self.client.post(
            reverse('user_profile:add_address_ajax'),
            {
                'full_name': 'John Doe',
                # Missing phone and other fields
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('required fields', data['error'])

    def test_edit_address_ajax_success(self):
        # Create an address first
        address = Address.objects.create(
            user=self.user,
            full_name='Old Name',
            phone='1234567890',
            address='Old Address',
            city='Old City',
            district='Old District',
            state='Old State',
            pincode='00000',
            is_default=True
        )

        response = self.client.post(
            reverse('user_profile:edit_address_ajax', kwargs={'pk': address.id}),
            {
                'full_name': 'New Name',
                'phone': '9876543210',
                'address': 'New Address',
                'city': 'New City',
                'district': 'New District',
                'state': 'New State',
                'pincode': '11111',
                'landmark': 'New Landmark',
                'is_default': 'on'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['address']['full_name'], 'New Name')
        self.assertEqual(data['address']['pincode'], '11111')

        # Refresh from DB
        address.refresh_from_db()
        self.assertEqual(address.full_name, 'New Name')
        self.assertEqual(address.pincode, '11111')

    def test_add_address_redirect_with_next(self):
        response = self.client.post(
            reverse('user_profile:add_address') + '?next=/orders/checkout/',
            {
                'full_name': 'Standard Doe',
                'mobile_number': '1234567890',
                'address': '123 Main Street',
                'city': 'Metropolis',
                'district': 'District 1',
                'state': 'New York',
                'pin_code': '10001',
                'landmark': 'Near Park',
                'is_default': 'on'
            }
        )
        self.assertRedirects(response, '/orders/checkout/', fetch_redirect_response=False)

    def test_edit_address_redirect_with_next(self):
        address = Address.objects.create(
            user=self.user,
            full_name='Old Name',
            phone='1234567890',
            address='Old Address',
            city='Old City',
            district='Old District',
            state='Old State',
            pincode='00000',
            is_default=True
        )
        response = self.client.post(
            reverse('user_profile:edit_address', kwargs={'pk': address.id}) + '?next=/orders/checkout/',
            {
                'full_name': 'New Standard Name',
                'phone': '9876543210',
                'address': 'New Address',
                'city': 'New City',
                'district': 'New District',
                'state': 'New State',
                'pincode': '11111',
                'landmark': 'New Landmark',
                'is_default': 'on'
            }
        )
        self.assertRedirects(response, '/orders/checkout/', fetch_redirect_response=False)
