import uuid
import keyword

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


IDENTIFIER_VALIDATOR = RegexValidator(
    regex=r'^[a-zA-Z_][a-zA-Z_]*$',
    message=_("Can only contain the letters a-z and underscores."))


def non_python_keyword(value):
    if keyword.iskeyword(value):
        raise ValidationError(
            _("This field is invalid as its value is forbidden.")
        )
    return value


def check_uuid(uid=None):
    if not uid:
        raise ValidationError(_("UUID not provided."))

    if uid and type(uid) is not uuid.UUID:
        try:
            uid = uuid.UUID(uid)
        except ValueError:
            raise ValidationError(_("UUID invalid."))
        return uid
    return uid
