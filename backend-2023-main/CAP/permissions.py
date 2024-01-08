from rest_framework.permissions import BasePermission
from Users.models import Profile

class IsCA(BasePermission):
    def has_permission(self, request, view):
        try:
            profile = Profile.objects.get(rdv_id=request.user.username)
            return profile.is_ca
        except Profile.DoesNotExist:
            return False