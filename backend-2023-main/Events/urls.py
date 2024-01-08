from django.urls import path

from .views import *

urlpatterns = [
	path('events/', EventsView.as_view(), name="events"),
    path('event_by_id/', EventByIdView.as_view(), name="event_by_id"),
    path('events_by_tag/', EventsByTagView.as_view(), name="events_by_tag"),
]