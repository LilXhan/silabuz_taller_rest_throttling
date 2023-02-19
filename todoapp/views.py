from django.shortcuts import render

from .models import Todo
from .serializers import TodoSerializer

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import ModelViewSet

class TodoViewSet(ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializer

    throttle_classes = [UserRateThrottle]

    @action(detail=True, methods=["post"], throttle_classes=[UserRateThrottle])
    def example_adhoc_method(request, pk=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)