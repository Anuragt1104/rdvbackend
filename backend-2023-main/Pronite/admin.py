from django.contrib import admin
from .models import *

# Register your models here.

class SlotAdmin(admin.ModelAdmin):
    list_display = ('slot', 'pronite', 'start_time', 'end_time', 'capacity', 'booked')

    def slot(self, obj):
        return obj.pronite + str(obj.id)

class BookingAdmin(admin.ModelAdmin):
    search_fields = ('ticket_id',)
    list_display = ('user', 'slot', 'ticket_id', 'booking_time', 'cancelled', 'admitted', 'pass_emailed')
    list_filter = ('pass_emailed', 'slot__pronite')

admin.site.register(Slot, SlotAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(ScanningSchedule)