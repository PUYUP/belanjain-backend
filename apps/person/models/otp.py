import uuid

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.hashers import make_password
from django.core.validators import RegexValidator, ValidationError, validate_email
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.core.mail import BadHeaderError, EmailMultiAlternatives

from utils.validators import non_python_keyword
from apps.person.utils.general import random_string
from apps.person.utils.constant import OTP_IDENTIFIER

_RANDOM_STRING = random_string()
_PROJECT_NAME = settings.PROJECT_NAME
_User = get_user_model()


def _send_email(instance):
    subject = _("OTP Validation")
    from_email = '%s <hellopuyup@gmail.com>' % (_PROJECT_NAME)
    to = instance.email

    # Message
    text = _(
        "JANGAN BERIKAN KODE OTP ini kepada siapapun "
        "TERMASUK PIHAK %(site_name)s. Kode OTP Anda: " +
        instance.otp_code
    ) % {'site_name': _PROJECT_NAME}

    html = _(
        "JANGAN BERIKAN KODE OTP ini kepada siapapun "
        "TERMASUK PIHAK %(site_name)s.<br />"
        "Kode OTP Anda: "
        "<strong>" + instance.otp_code + "</strong>"
        "<br /><br />"
        "Salam, <br /> <strong>%(site_name)s</strong>"
    ) % {'site_name': _PROJECT_NAME}

    if subject and from_email:
        try:
            msg = EmailMultiAlternatives(subject, text, from_email, [to])
            msg.attach_alternative(html, "text/html")
            return msg.send()
        except BadHeaderError:
            raise ValidationError(_('Invalid header found.'))


class AbstractOTPCode(models.Model):
    """
    Send OTP Code with;
        :email
        :telephone (SMS or Voice Call)

    :attempt_allowed; how many max allowed invalid OTP Code
    :attempt_used; attempt left, if 0 must create new OTP Code
    :date_expired; OTP Code validity max date (default 2 hour)
    :is_expired; attempt exceed or date expired
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='otps',
                             related_query_name='otp')

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    date_updated = models.DateTimeField(auto_now=True, null=True)
    date_expired = models.DateTimeField(blank=True, null=True, editable=False)

    email = models.EmailField(null=True, blank=True)
    telephone = models.CharField(blank=True, null=True, max_length=14)
    otp_hash = models.CharField(max_length=255)
    otp_code = models.CharField(max_length=255)
    attempt_allowed = models.IntegerField(default=3)
    attempt_used = models.IntegerField(default=0)
    is_used = models.BooleanField()
    is_expired = models.BooleanField(default=False)
    identifier = models.SlugField(
        choices=OTP_IDENTIFIER,
        max_length=128, null=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z_][0-9a-zA-Z_]*$',
                message=_(
                    "Code can only contain the letters a-z, A-Z, digits, "
                    "and underscores, and can't start with a digit.")),
            non_python_keyword
        ]
    )

    class Meta:
        abstract = True
        app_label = 'person'
        verbose_name = _('OTP Code')
        verbose_name_plural = _('OTP Codes')

    def __str__(self):
        return self.otp_code

    def clean(self):
        if not self.pk:
            if self.email:
                try:
                    validate_email(self.email)
                except ValidationError as e:
                    raise ValidationError(_(e.message))

                # Validate each account has different email
                if _User.objects.filter(email=self.email, account__email_verified=True).exists():
                    raise ValidationError(_('Email has been used.'))

            if self.identifier not in dict(OTP_IDENTIFIER):
                raise ValidationError(
                    _('%s is not a valid choice.' % self.get_identifier_display()))

    # Start validation
    def _validate_save(self):
        self.save()
        self.refresh_from_db()
        return self

    def validate(self, *args, **kwargs):
        if self.is_used:
            raise ValidationError(_("Has used on %s" % (self.date_updated)))

        if self.is_expired:
            raise ValidationError(_("Has expired on %s" % (self.date_updated)))

        if timezone.now() >= self.date_expired:
            self.is_expired = True
            self._validate_save()

            raise ValidationError(
                _("OTP code expired on %s." % (self.date_expired)))

        if self.attempt_used >= self.attempt_allowed:
            self.is_expired = True
            self._validate_save()

            raise ValidationError(_("OTP code invalid. Attempt %s from %s allowed."
                                    % (self.attempt_used, self.attempt_allowed)))

        otp_code = kwargs.get('otp_code', None)
        if not otp_code:
            raise ValidationError(_("OTP code not provided."))

        if self.otp_code != otp_code:
            # increase 'attempt_used'
            self.attempt_used = F('attempt_used') + 1
            self._validate_save()

            raise ValidationError(_("OTP code invalid. Attempt %s from %s allowed."
                                    % (self.attempt_used, self.attempt_allowed)))

        # all passed and mark as used!
        self.is_used = True
        self.save()
        self.refresh_from_db()

    def save(self, *args, **kwargs):
        # Set email from user email
        user_email = getattr(self.user, 'email', None)
        if user_email:
            self.email = user_email

        # After used can't change again
        if not self.pk:
            self.otp_code = _RANDOM_STRING
            self.otp_hash = make_password(_RANDOM_STRING)

            # Set max validity date
            # Default 2 hours since created
            self.date_expired = timezone.now() + timezone.timedelta(hours=2)
        super().save(*args, **kwargs)
