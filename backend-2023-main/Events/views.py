from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Event, Tag
from .serializers import EventSerializer
from django.db.models import Prefetch
from django.db.models import Count

class EventsView(APIView):
    def get(self, request):
        events = Event.objects.prefetch_related('tags')

        events_by_type_and_tags = {}

        for event in events:
            event_type = event.type
            event_tags = [tag.name for tag in event.tags.all()]

            if event_type not in events_by_type_and_tags:
                events_by_type_and_tags[event_type] = {}

            for tag_name in event_tags:
                if tag_name not in events_by_type_and_tags[event_type]:
                    events_by_type_and_tags[event_type][tag_name] = []
                events_by_type_and_tags[event_type][tag_name].append(EventSerializer(event).data)

        return Response(events_by_type_and_tags, status=status.HTTP_200_OK)


class EventByIdView(APIView):
    def get(self, request):
        event_id  = request.GET.get('event_id')
        event = get_object_or_404(Event, id=event_id)
        related_events = Event.objects.filter(tags__in=event.tags.all()).exclude(id=event.id).annotate(shared_tags=Count('tags')).order_by('-shared_tags')

        event_serializer = EventSerializer(event)
        related_events_serializer = EventSerializer(related_events, many=True)

        response_data = {
            'event': event_serializer.data,
            'related_events': related_events_serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)
    

class EventsByTagView(APIView):
    def get(self, request):
        tag_name  = request.GET.get('tag_name')
        tag = get_object_or_404(Tag, name=tag_name)
        events = Event.objects.filter(tags__in=[tag])

        events_serializer = EventSerializer(events, many=True)

        return Response(events_serializer.data, status=status.HTTP_200_OK)