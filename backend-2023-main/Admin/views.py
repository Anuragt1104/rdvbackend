from django.shortcuts import get_object_or_404
from collections import defaultdict
from itertools import chain

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import 	IsAuthenticated, IsAdminUser

from rest_framework import status
from CAP.models import *
from Users.models import Profile, College
from CAP.serializers import *
from .serializers import *
from .tasks import send_notification

from django.db.models import Min
from django.db.models.functions import Coalesce
from datetime import datetime
from django.utils import timezone

class AdminProfileView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        user = User.objects.get(username=request.user.username)
        serializer = AdminProfileSerializer(user)
        return Response(serializer.data)

class TaskView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        tasks = Task.objects.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

class SubmissionView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        task_id = request.GET.get('task_id')
        submissions = chain(Submission.objects.filter(status='UR', task=task_id).order_by('datetime_of_submission'), 
                            Submission.objects.filter(task=task_id).exclude(status='UR').order_by('datetime_of_submission'))

        rdv_submission_data = defaultdict(lambda: {'name': '', 'ca_id': '', 'college_name': '', 'points': '', 'submissions': defaultdict(list)})

        for submission in submissions:
            rdv_id = submission.user.rdv_id
            if not rdv_submission_data[rdv_id]['name']:
                rdv_submission_data[rdv_id]['name'] = submission.user.name
                rdv_submission_data[rdv_id]['ca_id'] = submission.user.ca_id
                rdv_submission_data[rdv_id]['college_name'] = College.objects.get(college_id=submission.user.college_id).college_name
                rdv_submission_data[rdv_id]['points'] = PointsLedger.objects.get(user=submission.user.id).points

            platform = submission.platform_category
            submission_data = {
                'id': submission.id,
                'date': submission.datetime_of_submission.date(),
                'time': submission.datetime_of_submission.time(),
                'status': submission.status,
                'points': submission.points,
                'images': []
            }

            submission_images = SubmissionImage.objects.filter(submission=submission)
            for image in submission_images:
                image_serializer = SubmissionImageSerializer(image)
                submission_data['images'].append(image_serializer.data)

            rdv_submission_data[rdv_id]['submissions'][platform].append(submission_data)

        return Response(rdv_submission_data)
    
    def post(self, request):
        submission_id = request.data.get('submission_id')
        points = request.data.get('points')

        try:
            submission = Submission.objects.get(id=submission_id)
        except Submission.DoesNotExist:
            return Response({'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)

        if points == 0:
            submission.status = 'RJ'
        else:
            submission.status = 'AP'
            submission.points = points

            pointsledger = PointsLedger.objects.get(user=submission.user)

            pointsledger.points += int(points)
            pointsledger.save()
        
        submission.save()
        return Response({'message': 'Submission updated successfully'})


class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        top_cas = (
            PointsLedger.objects.annotate(last_submission_time=Coalesce(Min('user__submission__datetime_of_submission'), timezone.now()))
            .order_by('-points', 'last_submission_time')
        )

        c_list = College.objects.all().values()
        college_list = {c['college_id']: c['college_name'] for c in c_list}

        p_list = Profile.objects.all().values()
        profile_list = {p['id']: (p['name'], p['college_id']) for p in p_list}

        leaderboard_data = []

        for rank, ca in enumerate(top_cas, start=1):
            data = {
                'Name': profile_list.get(ca.user_id)[0],
                'Points': ca.points,
                'College Name': college_list.get(profile_list.get(ca.user_id)[1]),
                'Rank': rank,
            }
            leaderboard_data.append(data)
        
        return Response(leaderboard_data)
    
class NotificationView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def post(self, request):
        serializer = NotificationSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save(created_by = request.user)

        send_notification.delay(serializer.data['id'])

        return Response(serializer.data, status=201)

class MessagesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    def get(self, request):
        if 'receiver' in request.GET:
            receiver = request.GET.get('receiver')
            messages = Message.objects.filter(sender=receiver) | Message.objects.filter(receiver=receiver)
            messages = messages.order_by('-datetime_of_sending')
            serializer = MessageSerializer(messages, many=True)
            return Response(serializer.data)
        else:
            users = Message.objects.values_list('sender', 'receiver')
            users = chain(*users)
            users = list(set(users))

            if 'admin' in users:
                users.remove('admin')

            info = []
            for ca_id in users:
                user = Profile.objects.get(ca_id=ca_id)

                latest_message = Message.objects.filter(sender=ca_id) | Message.objects.filter(receiver=ca_id)
                latest_message = latest_message.order_by('-datetime_of_sending').first()

                if latest_message:
                    serializer = MessageSerializer(latest_message)
                    users_info = {'name': user.name, 'ca_id': user.ca_id, 'latest_message': serializer.data}
                
                info.append(users_info)

            return Response(info)

    def post(self, request):
        receiver = request.data.get('receiver')
        message = request.data.get('message')
        serializer = MessageSerializer(data={'sender': 'admin', 'receiver': receiver, 'message': message})
        
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({'message': 'Message sent successfully'}, status=status.HTTP_201_CREATED)
    
class CreateTaskView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "Task created successfully"}, status=status.HTTP_201_CREATED)
    
class DeleteTaskView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request):
        task = get_object_or_404(Task, id=request.data.get('task_id'))

        task.delete()
        return Response({"detail": "Task deleted successfully"}, status=status.HTTP_204_NO_CONTENT)