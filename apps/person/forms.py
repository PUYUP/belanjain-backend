import itertools

from django import forms
from django.db.models import Prefetch
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from utils.generals import get_model
from apps.person.utils.constant import ROLE_IDENTIFIERS, REGISTERED
from apps.person.utils.auth import set_roles, update_roles

Role = get_model('person', 'Role')
RoleCapabilities = get_model('person', 'RoleCapabilities')

try:
    _ROLE_IDENTIFIERS = ROLE_IDENTIFIERS
except NameError:
    _ROLE_IDENTIFIERS = list()


try:
    _REGISTERED = REGISTERED
except NameError:
    _REGISTERED = list()


class UserChangeFormExtend(UserChangeForm):
    """ Override user Edit form """
    email = forms.EmailField(max_length=254, help_text=_(
        "Required. Inform a valid email address."))
    role = forms.MultipleChoiceField(
        choices=_ROLE_IDENTIFIERS,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text=_("Select roles for user."))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial =  list(self.instance.roles.all().values_list('identifier', flat=True))

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        username = self.cleaned_data.get('username', None)

        # Make user email filled
        if email:
            # Validate each account has different email
            if User.objects.filter(email=email).exclude(
                    username=username).exists():
                raise forms.ValidationError(_('Email has been used.'))
        return email

    def clean_role(self):
        role = self.cleaned_data.get('role', None)
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        
        roles = self.cleaned_data.get('role', None)
        if roles:
            update_roles(user=user, roles=roles)
        return user


class UserCreationFormExtend(UserCreationForm):
    """ Override user Add form """
    email = forms.EmailField(max_length=254, help_text=_(
        "Required. Inform a valid email address."))
    role = forms.MultipleChoiceField(
        choices=_ROLE_IDENTIFIERS,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text=_("Select roles for user."))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = _REGISTERED

    def clean_email(self):
        email = self.cleaned_data.get('email', None)
        username = self.cleaned_data.get('username', None)

        # Make user email filled
        if email:
            # Validate each account has different email
            if User.objects.filter(email=email).exclude(
                    username=username).exists():
                raise forms.ValidationError(
                    _('Email has been used.'),
                    otp_code='email_used',
                )
        return email

    def save(self, commit=True):
        user = super().save(commit=True)
        if commit:
            user.save()

        # ADD ROLES
        roles = self.cleaned_data.get('role', None)
        if roles:
            set_roles(user=user, roles=roles)
        return user
