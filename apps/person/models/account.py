import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import validate_email

from utils.generals import get_model
from apps.person.utils.constant import EMAIL_VALIDATION, TELEPHONE_VALIDATION


# Create your models here.
class AbstractAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='account')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(blank=True, null=True, max_length=14)

    email_verified = models.BooleanField(default=False, null=True)
    telephone_verified = models.BooleanField(default=False, null=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")

    def __str__(self):
        return self.user.username

    def validate_email(self, *args, **kwargs):
        if self.email_verified == True:
            raise ValidationError(_("Email has verified."))

        OTPCode = get_model('person', 'OTPCode')
        try:
            OTPCode.objects \
                .filter(email=self.email, is_used=True, identifier=EMAIL_VALIDATION) \
                .latest('date_created')
        except ObjectDoesNotExist:
            raise ValidationError(_("OTP code invalid."))
        self.email_verified = True
        self.save()

    def validate_telephone(self, *args, **kwargs):
        if self.telephone_verified == True:
            raise ValidationError(_("Telephone has verified."))

        OTPCode = get_model('person', 'OTPCode')
        try:
            OTPCode.objects \
                .filter(telephone=self.telephone, is_used=True,
                        identifier=TELEPHONE_VALIDATION) \
                .latest('date_created')
        except ObjectDoesNotExist:
            raise ValidationError(_("OTP code invalid."))
        self.telephone_verified = True
        self.save()


class AbstractProfile(models.Model):
    _UPLOAD_TO = 'images/user'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='profile')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)

    biography = models.TextField(blank=True, null=True)
    picture = models.ImageField(upload_to=_UPLOAD_TO, max_length=500, null=True,
                                blank=True)

    class Meta:
        abstract = True
        app_label = 'person'
        ordering = ['-user__date_joined']
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        return self.user.username
