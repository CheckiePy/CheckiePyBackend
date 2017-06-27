from django.utils import timezone

from code_style import models as code_style_models
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import models
from . import tasks
from . import serializers


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def update(request):
    last_update = models.GitRepositoryUpdate.objects.filter(user=request.user).order_by('-datetime').first()
    if last_update and last_update.datetime > timezone.now() - timezone.timedelta(seconds=3):
        return Response(False, status.HTTP_200_OK)
    update = models.GitRepositoryUpdate.objects.create(user=request.user)
    tasks.load_user_repositories.delay(request.user.username, update.id)
    return Response(True, status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def repository_list(request):
    repositories = models.GitRepository.objects.filter(user=request.user)
    serializer = serializers.GitRepositorySerializer(repositories, many=True)
    return Response({'result': serializer.data}, status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def last_update(request):
    last_update = models.GitRepositoryUpdate.objects.filter(user=request.user).order_by('-datetime').first()
    serializer = serializers.GitRepositoryUpdateSerializer(last_update)
    return Response(serializer.data, status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def connect_repository(request):
    serializer = serializers.GitRepositoryConnectionSerializer(data=request.data)
    print(serializer)
    if serializer.is_valid():
        repository = models.GitRepository.objects.filter(id=serializer.data['repository']).first()
        if repository.is_connected:
            return Response({'detail': 'Repository already connected'}, status.HTTP_400_BAD_REQUEST)
        code_style = code_style_models.CodeStyle.objects.filter(id=serializer.data['code_style']).first()
        models.GitRepositoryConnection.objects.create(repository=repository, code_style=code_style)
        tasks.set_hook.delay(request.user.username, repository.id)
        return Response({'result': serializer.data}, status.HTTP_200_OK)
    return Response({'detail': 'Required fields does not specified or objects does not exists'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def handle_hook(request, id):
    tasks.handle_hook.delay(request.body.decode(), id)
    return Response(True, status.HTTP_200_OK)
