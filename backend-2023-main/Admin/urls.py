from django.urls import path

from .views import *

urlpatterns = [
    path('profile/', AdminProfileView.as_view(), name="admin_profile"),
    path('task/', TaskView.as_view(), name="task"),
    path('submission/', SubmissionView.as_view(), name="submission"),
	path('leaderboard/', LeaderboardView.as_view(), name="leaderboard"),
    path('notifs/', NotificationView.as_view(), name="notifications"),
    path('messages/', MessagesView.as_view(), name="messages"),
    path('create_task/', CreateTaskView.as_view(), name='create-task'),
    path('delete_task/', DeleteTaskView.as_view(), name='delete-task'),
]