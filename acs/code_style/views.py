from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import serializers
from . import tasks
from . import models


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def create(request, format=None):
    serializer = serializers.CodeStyleSerializer(data=request.data)
    if serializer.is_valid():
        code_style = models.CodeStyle.objects.create(user=request.user, name=serializer.data['name'], repository=serializer.data['repository'])
        tasks.calc_metrics.delay(code_style.id)
        response = True
    else:
        response = serializer.errors
    return Response(response, status=status.HTTP_200_OK)