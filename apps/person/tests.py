from django.test import TestCase
from django.contrib.auth.models import User

from utils.generals import get_model

Account = get_model('person', 'Account')
Profile = get_model('person', 'Profile')
OTPCode = get_model('person', 'OTPCode')


# Create your tests here.
class AccountTestCase(TestCase):
    def setUp(self):
        self.email = 'test@email.com'
        self.telephone = '0811806807'

        self.user = User.objects.create_user('testuser', 'my@wmail.com', '123456')
        self.otp_code_email = OTPCode.objects.create(email=self.email, is_used=False, is_expired=False)
        self.otp_code_telephone = OTPCode.objects.create(telephone=self.telephone, is_used=False, is_expired=False)

    def test_account_created(self):
        account = Account.objects.get(user__id=self.user.id)
        profile = Profile.objects.get(user__id=self.user.id)
        otp_code_email = OTPCode.objects.get(email=self.email)
        otp_code_telephone = OTPCode.objects.get(telephone=self.telephone)

        self.assertEqual(self.user.account, account)
        self.assertEqual(self.user.profile, profile)

        self.assertEqual(self.otp_code_email, otp_code_email)
        self.assertEqual(self.otp_code_telephone, otp_code_telephone)

    def test_validate_otp_code(self):
        otp_code_valid_email = OTPCode.objects.validate(email=self.email, otp_code=self.otp_code_email.otp_code)
        otp_code_valid_telephone = OTPCode.objects.validate(telephone=self.telephone, otp_code=self.otp_code_telephone.otp_code)

        self.assertEqual(otp_code_valid_email, True)
        self.assertEqual(otp_code_valid_telephone, True)
