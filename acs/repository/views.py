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
from code_style import serializers as code_style_serializers


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def update_repository(request):
    last_update = models.GitRepositoryUpdate.objects.filter(user=request.user).order_by('-datetime').first()
    if last_update and last_update.datetime > timezone.now() - timezone.timedelta(seconds=3):
        return Response({'detail': 'Updates requested too ofter. Please, try again later'}, status.HTTP_400_BAD_REQUEST)
    update = models.GitRepositoryUpdate.objects.create(user=request.user)
    tasks.load_user_repositories.delay(request.user.username, update.id)
    return Response({'result': 'Repository update was started'}, status.HTTP_200_OK)


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
def last_repository_update(request):
    last_update = models.GitRepositoryUpdate.objects.filter(user=request.user).order_by('-datetime').first()
    serializer = serializers.GitRepositoryUpdateSerializer(last_update)
    return Response(serializer.data, status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def connect_repository(request):
    serializer = serializers.GitRepositoryConnectionSerializer(data=request.data)
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
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def disconnect_repository(request):
    serializer = code_style_serializers.IdSerializer(data=request.data)
    if serializer.is_valid():
        connection = models.GitRepositoryConnection.objects.filter(repository=serializer.data['id']).first()
        if not connection:
            return Response({'detail': 'Repository connection not found'}, status.HTTP_404_NOT_FOUND)
        # Todo: github request to delete webhook
        connection.repository.is_connected = False
        connection.repository.save()
        connection.delete()
        return Response({'result': serializer.data['id']}, status.HTTP_200_OK)
    return Response({'detail': 'You should specify repository id'}, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def handle_hook(request, id):
    tasks.handle_hook.delay(request.body.decode(), id)
    return Response(True, status.HTTP_200_OK)
