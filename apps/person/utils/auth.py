import itertools

from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from utils.generals import get_model

UserModel = get_user_model()


class CurrentUserDefault:
    """Return current logged-in user"""
    def set_context(self, serializer_field):
        user = serializer_field.context['request'].user
        self.user = user

    def __call__(self):
        return self.user

    def __repr__(self):
        return '%s()' % self.__class__.__name__


class LoginBackend(ModelBackend):
    """Login w/h username or email"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        try:
            # user = UserModel._default_manager.get_by_natural_key(username)
            # You can customise what the given username is checked against, here I compare to both username and email fields of the User model
            user = UserModel.objects \
                .filter(
                    Q(username__iexact=username)
                    | Q(email__iexact=username)
                    | Q(account__telephone=username)
                    & Q(account__telephone_verified=True))
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            try:
                user = user.get(Q(username__iexact=username) | Q(email__iexact=username)
                                | Q(account__telephone=username)
                                & Q(account__telephone_verified=True))
            except UserModel.DoesNotExist:
                return None

            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
        return super().authenticate(request, username, password, **kwargs)


def set_roles(user=None, roles=list()):
    """
    :user is user object
    :roles is list of identifier for role, egg: ['registered', 'customer']
    """
    RoleCapabilities = get_model('person', 'RoleCapabilities')

    roles_created = list()
    identifiers_initial = list(user.roles.values_list('identifier', flat=True))
    identifiers_new = list(set(roles) - set(identifiers_initial))

    for identifier in identifiers_new:
        role_obj = user.roles.model(user_id=user.id, identifier=identifier)
        roles_created.append(role_obj)

    if roles_created:
        user.roles.model.objects.bulk_create(roles_created)

    capabilities_objs = RoleCapabilities.objects \
        .prefetch_related(Prefetch('permissions')) \
        .filter(identifier__in=user.roles.all().values('identifier'))
    permission_objs = [list(item.permissions.all()) for item in capabilities_objs]
    permission_objs_unique = list(set(itertools.chain.from_iterable(permission_objs)))
    user.user_permissions.add(*permission_objs_unique)


def update_roles(user=None, roles=list()):
    """
    :user is user object
    :roles is list of identifier for role, egg: ['registered', 'customer']
    """
    RoleCapabilities = get_model('person', 'RoleCapabilities')

    permissions_removed = list()
    permissions_add = list()
    permissions_current = user.user_permissions.all()
    capabilities = RoleCapabilities.objects \
        .prefetch_related(Prefetch('permissions'))

    # REMOVE ROLES
    roles_removed = user.roles.exclude(identifier__in=roles)
    if roles_removed.exists():
        capabilities = capabilities.filter(identifier__in=roles_removed.values('identifier'))
        permissions = [list(item.permissions.all()) for item in capabilities]
        permissions_removed = list(set(itertools.chain.from_iterable(permissions)))
        roles_removed.delete()

    # ADD ROLES
    if roles:
        roles_created = list()
        identifiers_initial = list(user.roles.values_list('identifier', flat=True))
        identifiers_new = list(set(roles) ^ set(identifiers_initial))

        for identifier in identifiers_new:
            role_obj = user.roles.model(user_id=user.id, identifier=identifier)
            roles_created.append(role_obj)

        if roles_created:
            user.roles.model.objects.bulk_create(roles_created)

        capabilities = capabilities.filter(identifier__in=user.roles.all().values('identifier'))
        permissions = [list(item.permissions.all()) for item in capabilities]
        permissions_add = list(set(itertools.chain.from_iterable(permissions)))

    # Compare current with new permissions
    # If has different assign that to user
    if permissions_current:
        add_diff = list(set(permissions_add) & set(permissions_current))
        if add_diff:
            add_diff = list(set(permissions_add) ^ set(add_diff))
    else:
        add_diff = list(set(permissions_add))

    if add_diff and permissions_add:
        user.user_permissions.add(*list(add_diff))

    # Compare current with old permissions
    # If has different remove that
    removed_diff = list(set(permissions_add) ^ set(permissions_removed))
    if removed_diff and permissions_removed:
        diff = set(removed_diff) & set(permissions_removed)
        user.user_permissions.remove(*list(diff))
