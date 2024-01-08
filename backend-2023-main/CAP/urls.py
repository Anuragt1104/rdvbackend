from django.urls import path

from .views import *

urlpatterns = [
	path('leaderboard/', LeaderboardView.as_view(), name="leaderboard"),
    path('tasks/', GetTasksView.as_view(), name="tasks"),
    path('task_upload/', TaskUploadView.as_view(), name="task-upload"),
    path('notifs/', NotificationsView.as_view(), name="notifications"),
    path('messages/', MessagesView.as_view(), name="messages"),
]