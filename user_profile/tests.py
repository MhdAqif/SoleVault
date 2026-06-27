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
                'phone': '9876543210',
                'address': '123 Main Street',
                'city': 'Metropolis',
                'district': 'District One',
                'state': 'New York',
                'pincode': '110001',
                'landmark': 'Near Park',
                'is_default': 'on'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['address']['full_name'], 'John Doe')
        self.assertEqual(data['address']['pincode'], '110001')
        self.assertTrue(data['address']['is_default'])

        # Verify it was saved in DB
        self.assertTrue(Address.objects.filter(user=self.user, pincode='110001').exists())

    def test_add_address_ajax_missing_fields(self):
        response = self.client.post(
            reverse('user_profile:add_address_ajax'),
            {
                'full_name': 'John Doe',
                # Missing phone and other fields
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertTrue('error' in data)

    def test_edit_address_ajax_success(self):
        # Create an address first
        address = Address.objects.create(
            user=self.user,
            full_name='Old Name',
            phone='9876543210',
            address='Old Address',
            city='Old City',
            district='Old District',
            state='Old State',
            pincode='110001',
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
                'pincode': '110002',
                'landmark': 'New Landmark',
                'is_default': 'on'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['address']['full_name'], 'New Name')
        self.assertEqual(data['address']['pincode'], '110002')

        # Refresh from DB
        address.refresh_from_db()
        self.assertEqual(address.full_name, 'New Name')
        self.assertEqual(address.pincode, '110002')

    def test_add_address_redirect_with_next(self):
        response = self.client.post(
            reverse('user_profile:add_address') + '?next=/orders/checkout/',
            {
                'full_name': 'Standard Doe',
                'mobile_number': '9876543210',
                'address': '123 Main Street',
                'city': 'Metropolis',
                'district': 'District One',
                'state': 'New York',
                'pin_code': '110001',
                'landmark': 'Near Park',
                'is_default': 'on'
            }
        )
        self.assertRedirects(response, '/orders/checkout/', fetch_redirect_response=False)

    def test_edit_address_redirect_with_next(self):
        address = Address.objects.create(
            user=self.user,
            full_name='Old Name',
            phone='9876543210',
            address='Old Address',
            city='Old City',
            district='Old District',
            state='Old State',
            pincode='110001',
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
                'pincode': '110002',
                'landmark': 'New Landmark',
                'is_default': 'on'
            }
        )
        self.assertRedirects(response, '/orders/checkout/', fetch_redirect_response=False)


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.login(username='testuser@example.com', password='testpassword')

    def test_registered_user_change_password_view(self):
        response = self.client.get(reverse('user_profile:change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update Password')
        self.assertNotContains(response, "You're signed in with Google")

    def test_google_sso_user_change_password_view(self):
        from allauth.socialaccount.models import SocialAccount
        SocialAccount.objects.create(
            user=self.user,
            provider='google',
            uid='123456789'
        )
        response = self.client.get(reverse('user_profile:change_password'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You're signed in with Google")
        self.assertNotContains(response, 'Update Password')

        # Try to POST
        response = self.client.post(reverse('user_profile:change_password'), {'password': 'newpassword'})
        self.assertEqual(response.status_code, 302) # Redirects


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        self.client.login(username='testuser@example.com', password='testpassword')

    def test_profile_update_success(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        avatar = SimpleUploadedFile("avatar.jpg", small_gif, content_type="image/jpeg")

        response = self.client.post(
            reverse('user_profile:profile'),
            {
                'full_name': 'New User Name',
                'phone': '9876543210',
                'email': 'testuser@example.com',
                'photo': avatar,
                'remove_photo': '0'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'User Name')
        self.assertTrue(self.user.profile_image)
        self.assertTrue(self.user.profile_image.name.startswith('profile_images/'))

    def test_profile_remove_photo(self):
        # Set a dummy profile image first
        self.user.profile_image = 'profile_images/dummy.jpg'
        self.user.save()

        response = self.client.post(
            reverse('user_profile:profile'),
            {
                'full_name': 'Test User',
                'phone': '9876543210',
                'email': 'testuser@example.com',
                'remove_photo': '1'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.profile_image)


