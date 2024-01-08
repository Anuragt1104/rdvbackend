from rest_framework.permissions import BasePermission

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser
        
class IsShashank(BasePermission):
    def has_permission(self, request, view):
        return request.user.username == 'shashank' or request.user.username == 'rendezvous'