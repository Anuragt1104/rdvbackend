from django.shortcuts import get_object_or_404
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import 	IsAuthenticated
from .permissions import IsCA

from rest_framework import status
from .models import *
from Users.models import Profile, College
from .serializers import *

from django.db.models import Min
from django.db.models.functions import Coalesce

class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated, IsCA]
    def get(self, request):
        top_cas = (
            PointsLedger.objects.annotate(last_submission_time=Coalesce(Min('user__submission__datetime_of_submission'), datetime.now()))
            .order_by('-points', 'last_submission_time')[:20]
        )
        leaderboard_data = []
        
        for rank, ca in enumerate(top_cas, start=1):
            data = {
                'Name': ca.user.name,
                'Points': ca.points,
                'College Name': College.objects.get(college_id=ca.user.college_id).college_name,
                'Rank': rank,
            }
            leaderboard_data.append(data)
        
        return Response(leaderboard_data)
    
class GetTasksView(APIView):
    permission_classes = [IsAuthenticated, IsCA]

    def get(self, request):
        tasks = Task.objects.filter(deadline__gt=datetime.now()).order_by('deadline')
        user = get_object_or_404(Profile, rdv_id = request.user.username)

        task_data = []
        for task in tasks:
            has_submitted = Submission.objects.filter(user=user, task=task).exists()
            serializer = TaskSerializer(task)
            task_info = serializer.data
            task_info['has_submitted'] = has_submitted
            task_data.append(task_info)

        return Response(task_data)

class TaskUploadView(APIView):
    permission_classes = [IsAuthenticated, IsCA]
    def post(self, request):
        user = get_object_or_404(Profile, rdv_id = request.user.username)
        task_id = request.data.get('task_id')
        platform_category = request.data.get('platform_category')
        images = request.data.getlist('images')
        
        serializer = SubmissionSerializer(data={'user': user.id, 'platform_category': platform_category, 'task': task_id})
        
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()
        
        for image in images:
            img_serializer = SubmissionImageSerializer(data={'submission': submission.id, 'image': image})
            
            img_serializer.is_valid(raise_exception=True)
            img_serializer.save()
        
        return Response({'message': 'Submission created successfully'}, status=status.HTTP_201_CREATED)

class NotificationsView(APIView):
    permission_classes = [IsAuthenticated, IsCA]
    def get(self, request):
        notifications = Notification.objects.all()
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
class MessagesView(APIView):
    permission_classes = [IsAuthenticated, IsCA]
    def get(self, request):
        user = get_object_or_404(Profile, rdv_id = request.user.username)
        messages = Message.objects.filter(sender=user.ca_id) | Message.objects.filter(receiver=user.ca_id)
        messages = messages.order_by('-datetime_of_sending')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = get_object_or_404(Profile, rdv_id = request.user.username)
        message = request.data.get('message')
        serializer = MessageSerializer(data={'sender': user.ca_id, 'receiver': 'admin', 'message': message})
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'message': 'Message sent successfully'}, status=status.HTTP_201_CREATED)