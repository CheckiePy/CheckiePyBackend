from django.utils import timezone

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import models
from . import tasks


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def update(request, format=None):
    last_update = models.GitRepositoryUpdate.objects.filter(user=request.user).order_by('-datetime').first()
    if last_update and last_update.datetime > timezone.now() - timezone.timedelta(seconds=3):
        return Response(False, status.HTTP_200_OK)
    update = models.GitRepositoryUpdate.objects.create(user=request.user)
    tasks.load_user_repositories.delay(request.user.username, update.id)
    return Response(True, status.HTTP_200_OK)