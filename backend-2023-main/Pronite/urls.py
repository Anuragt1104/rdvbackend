from django.urls import path
from .views import *

urlpatterns = [
    path('slot/', SlotView.as_view(), name='slot'),
    path('active/', ProniteView.as_view(), name='active_pronite'),
    path('slot/<int:id>/', SlotView.as_view(), name='slot_delete'),
    path('book/', BookingView.as_view(), name='book_pass'),
    path('send_passes/', SendPassView.as_view(), name='send_passes'),
    path('scan_pass/', ScanPassView.as_view(), name='scan_pass'),
    path('create_pass_id/', CreatePassbyIDView.as_view(), name='create_pass_id'),
    path('create_pass_email/', CreatePassbyEmailView.as_view(), name='create_pass_email'),
    path('cancel_pass/', CancelPassView.as_view(), name='cancel_pass'),
    path('block_user/', BlockUserView.as_view(), name='block_user'),
    path('download/', DownloadPassView.as_view(), name='download_pass'),
    path('scanslot/', ScanSlotView.as_view(), name='scanslot'),
    path('scanslot/<int:id>/', ScanSlotView.as_view(), name='scanslot_delete'),
    path('logs/', LogView.as_view(), name='logs'),
]