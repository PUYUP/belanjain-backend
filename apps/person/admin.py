from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q, Prefetch
from django.contrib.auth.models import User

from utils.generals import get_model
from apps.person.forms import UserChangeFormExtend, UserCreationFormExtend
from apps.person.utils.constant import ROLE_IDENTIFIERS

Profile = get_model('person', 'Profile')
Account = get_model('person', 'Account')
Role = get_model('person', 'Role')
RoleCapabilities = get_model('person', 'RoleCapabilities')
OTPCode = get_model('person', 'OTPCode')

try:
    _ROLE_LENGTH = len(ROLE_IDENTIFIERS)
except NameError:
    _ROLE_LENGTH = 0


class ProfileInline(admin.StackedInline):
    model = Profile


class AccountInline(admin.StackedInline):
    model = Account
    readonly_fields = ('email',)


class RoleCapabilitiesExtend(admin.ModelAdmin):
    model = RoleCapabilities
    filter_horizontal = ('permissions',)


class UserExtend(UserAdmin):
    _INLINE_SET = [ProfileInline, AccountInline]

    form = UserChangeFormExtend
    add_form = UserCreationFormExtend
    inlines = _INLINE_SET
    list_display = ('username', 'first_name', 'email', 'telephone', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'email',)}),
        (_("Personal info"), {'fields': ('first_name', 'last_name',)}),
        (_("Permissions"), {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser',),
        }),
        (_("Important dates"), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password1', 'password2', 'role',)
        }),
    )

    def telephone(self, obj):
        return obj.account.telephone
    telephone.short_description = _("Telephone")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        queryset = qs \
            .prefetch_related(Prefetch('account'), Prefetch('profile')) \
            .select_related('account', 'profile')
        return queryset


class OTPCodeExtend(admin.ModelAdmin):
    model = OTPCode
    list_display = ('email', 'telephone', 'otp_code', 'identifier',
                    'is_used', 'is_expired', 'attempt_used', 'otp_hash',)
    list_display_links = ('email', 'telephone',)
    readonly_fields = ('otp_code', 'otp_hash', 'date_expired',)

    def get_readonly_fields(self, request, obj=None):
        # Disallow edit
        if obj:
            return list(set(
                [field.name for field in self.opts.local_fields] +
                [field.name for field in self.opts.local_many_to_many]))
        return super().get_readonly_fields(request, obj)

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)


admin.site.unregister(User)
admin.site.register(User, UserExtend)
admin.site.register(RoleCapabilities, RoleCapabilitiesExtend)
admin.site.register(OTPCode, OTPCodeExtend)
