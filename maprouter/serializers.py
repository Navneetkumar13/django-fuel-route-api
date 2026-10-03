from rest_framework import serializers

class RouteRequestSerializer(serializers.Serializer):
    start = serializers.CharField(max_length=255, required=True)
    finish = serializers.CharField(max_length=255, required=True)