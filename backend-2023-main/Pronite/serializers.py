from rest_framework import serializers
from .models import *

class SlotSerializer(serializers.Serializer):
    pronite = serializers.CharField(max_length=1)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    capacity = serializers.IntegerField()
    eligibility = serializers.CharField(max_length=1)

    class Meta:
        fields = ("pronite", "start_time", "end_time", "capacity", "eligibility")

    def validate(self, data):
        pronite = data.get("pronite")
        start_time = data.get("start_time")
        end_time = data.get("end_time")
        capacity = data.get("capacity")
        eligibility = data.get("eligibility")

        if pronite is None or start_time is None or end_time is None or capacity is None:
            raise serializers.ValidationError("Missing data.")
        
        if pronite not in "SKMD":
            raise serializers.ValidationError("Invalid pronite.")
        
        if eligibility not in "ESFTX":
            raise serializers.ValidationError("Invalid eligibility.")

        if start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")
        
        if capacity <= 0:
            raise serializers.ValidationError("Capacity must be greater than 0.")
        
        if Slot.objects.filter(pronite=pronite, eligibility=eligibility, start_time__lt=start_time, end_time__gt=start_time).exists():
            raise serializers.ValidationError("Slot overlaps with existing slot.")
        if Slot.objects.filter(pronite=pronite, eligibility=eligibility, start_time__lt=end_time, end_time__gt=end_time).exists():
            raise serializers.ValidationError("Slot overlaps with existing slot.")

        return data

class ScanSlotSerializer(serializers.Serializer):
    pronite = serializers.CharField(max_length=1)
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()

    class Meta:
        fields = ("pronite", "start_time", "end_time")

    def validate(self, data):
        pronite = data.get("pronite")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if pronite is None or start_time is None or end_time is None:
            raise serializers.ValidationError("Missing data.")
        
        if pronite not in "SKMD":
            raise serializers.ValidationError("Invalid pronite.")

        if start_time >= end_time:
            raise serializers.ValidationError("Start time must be before end time.")
        
        if ScanningSchedule.objects.filter(pronite=pronite, start_time__lt=start_time, end_time__gt=start_time).exists():
            raise serializers.ValidationError("Slot overlaps with existing slot.")
        if ScanningSchedule.objects.filter(pronite=pronite, start_time__lt=end_time, end_time__gt=end_time).exists():
            raise serializers.ValidationError("Slot overlaps with existing slot.")

        return data