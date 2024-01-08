from django.contrib import admin
from .models import *

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('rdv_id', 'name', 'email', 'mobile_number', 'is_ca', 'ca_id', 'isVerified')
    search_fields = ('rdv_id', 'name', 'email', 'mobile_number', 'ca_id')
    list_filter = ('is_ca', 'BlockedFromPronite')

class CollegeAdmin(admin.ModelAdmin):
    search_fields = ('college_name', 'college_id')

admin.site.register(College, CollegeAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(TeamData)
admin.site.register(FacultyData)