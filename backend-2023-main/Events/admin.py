from django.contrib import admin
from .models import *


class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag_list')

class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_count')

admin.site.register(Event, EventAdmin)
admin.site.register(Tag, TagAdmin)