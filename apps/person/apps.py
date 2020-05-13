from django.apps import AppConfig
from django.db.models.signals import post_save


class PersonConfig(AppConfig):
    name = 'apps.person'

    def ready(self):
        from django.contrib.auth import get_user_model
        from utils.generals import get_model
        from apps.person.signals import user_save_handler, otpcode_save_handler

        User = get_user_model()
        OTPCode = get_model('person', 'OTPCode')

        post_save.connect(user_save_handler, sender=User, dispatch_uid='user_save_signal')
        post_save.connect(otpcode_save_handler, sender=OTPCode, dispatch_uid='otpcode_savee_signal')
