from rest_framework import serializers
from .models import Submission, SubmissionImage, Notification, Message, Task

class SubmissionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Submission
		fields ='__all__'
	
	def validate(self, data):
		user = data.get("user")
		task = data.get("task")
		
		if not task.multiple_uploads_allowed and Submission.objects.filter(user=user, task=task).exists():
			raise serializers.ValidationError("Multiple uploads not allowed for this task")
		
		return data

class SubmissionImageSerializer(serializers.ModelSerializer):
	class Meta:
		model = SubmissionImage
		fields ='__all__'

class NotificationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notification
		fields ='__all__'
    
	created_by = serializers.PrimaryKeyRelatedField(read_only=True)

class MessageSerializer(serializers.ModelSerializer):
	class Meta:
		model = Message
		fields ='__all__'

class TaskSerializer(serializers.ModelSerializer):
    
	class Meta:
		model = Task
		fields = '__all__'
