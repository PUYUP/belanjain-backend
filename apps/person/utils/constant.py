from django.utils.translation import ugettext_lazy as _

REGISTERED = 'registered'
CUSTOMER = 'customer'
OPERATOR = 'operator'
ROLE_IDENTIFIERS = (
    (REGISTERED, _("Registered")),
    (CUSTOMER, _("Customer")),
    (OPERATOR, _("Operator")),
)

ROLE_DEFAULTS = (
    (REGISTERED, _("Registered")),
    (CUSTOMER, _("Customer")),
)


EMAIL_VALIDATION = 'email_validation'
CHANGE_EMAIL_VALIDATION = 'change_email_validation'
TELEPHONE_VALIDATION = 'telephone_validation'
CHANGE_TELEPHONE_VALIDATION = 'change_telephone_validation'
REGISTER_VALIDATION = 'register_validation'
OTP_IDENTIFIER = (
    (EMAIL_VALIDATION, _("Email Validation")),
    (CHANGE_EMAIL_VALIDATION, _("Change Email Validation")),
    (TELEPHONE_VALIDATION, _("Telephone Validation")),
    (CHANGE_TELEPHONE_VALIDATION, _("Change Telephone Validation")),
    (REGISTER_VALIDATION, _("Register Validation")),
)
