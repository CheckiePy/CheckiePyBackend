from django.utils import timezone

from code_style import models as cs_models
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
    repositories = models.GitRepository.objects.all()
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
def set_hook(request, repo_id, code_style_id):
    try:
        repository = models.GitRepository.objects.get(id=repo_id)
        if not repository.is_connected:
            code_style = cs_models.CodeStyle.objects.get(id=code_style_id)
            models.GitRepositoryConnection.objects.create(repository=repository, code_style=code_style)
            tasks.set_hook.delay(request.user.username, repository.id)
            response = True
        else:
            response = False
    except Exception as e:
        print(e)
        response = False
    return Response(response, status.HTTP_200_OK)


@api_view(['POST'])
def handle_hook(request, id):
    tasks.handle_hook.delay(request.body.decode(), id)
    return Response(True, status.HTTP_200_OK)
