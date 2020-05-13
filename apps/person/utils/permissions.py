from rest_framework import permissions


class IsUserSelfOrReject(permissions.BasePermission):
    def has_permission(self, request, view):
        # id from url param
        user_id = int(view.kwargs.get('id', 0))
        return user_id == request.user.id
