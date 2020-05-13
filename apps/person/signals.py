import asyncio

from django.db.models import Q, F

from utils.generals import get_model
from apps.person.models.otp import _send_email
from apps.person.utils.constant import ROLE_DEFAULTS
from apps.person.utils.auth import set_roles

Account = get_model('person', 'Account')
Profile = get_model('person', 'Profile')
Role = get_model('person', 'Role')

_ASYNC_LOOP = asyncio.get_event_loop()


def user_save_handler(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance, email=instance.email)
        Profile.objects.create(user=instance)
        Role.objects.create(user=instance)

        # set default roles
        roles = list()
        for item in ROLE_DEFAULTS:
            roles.append(item[0])

        if roles:
            set_roles(user=instance, roles=roles)

    if not created:
        instance.account.email = instance.email
        instance.account.save()


def otpcode_save_handler(sender, instance, created, **kwargs):
    if instance.email:
        _ASYNC_LOOP.run_in_executor(None, _send_email, instance)

    if created:
        oldest = instance.__class__.objects \
            .filter(
                Q(identifier=instance.identifier),
                Q(is_used=False), Q(is_expired=False),
                Q(email=instance.email), Q(telephone=instance.telephone)) \
            .exclude(otp_code=instance.otp_code)

        if oldest:
            oldest.update(is_expired=True)
