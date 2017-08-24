from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import serializers
from . import tasks
from . import models
from repository import models as repository_models
from repository import tasks as repository_tasks


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def create_code_style(request):
    create_serializer = serializers.CodeStyleCreateSerializer(data=request.data)
    if create_serializer.is_valid():
        code_style = models.CodeStyle.objects.create(user=request.user, name=create_serializer.data['name'],
                                                     repository=create_serializer.data['repository'])
        try:
            tasks.calc_metrics.delay(code_style.id)
        except:
            code_style.calc_status = 'F'
            code_style.save()
            return Response({'detail': 'Cannot execute async operation'}, status.HTTP_412_PRECONDITION_FAILED)
        read_serializer = serializers.CodeStyleReadSerializer(code_style)
        return Response({'result': read_serializer.data}, status=status.HTTP_200_OK)
    return Response({'detail': 'Required fields does not specified'}, status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def code_style_list(request):
    code_styles = models.CodeStyle.objects.filter(user=request.user, calc_status='C')
    serializer = serializers.CodeStyleReadSerializer(code_styles, many=True)
    return Response({'result': serializer.data}, status.HTTP_200_OK)


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def read_code_style(request, id):
    code_style = models.CodeStyle.objects.filter(user=request.user, id=id).first()
    if not code_style:
        return Response({'detail': 'Code style not found'}, status.HTTP_404_NOT_FOUND)
    code_style_read_serializer = serializers.CodeStyleReadSerializer(code_style)
    return Response({'result': code_style_read_serializer.data}, status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def delete_code_style(request):
    serializer = serializers.IdSerializer(data=request.data)
    if serializer.is_valid():
        id = serializer.data['id']
        code_style = models.CodeStyle.objects.filter(id=id, user=request.user).first()
        if not code_style:
            return Response({'detail': 'Code style not found'}, status.HTTP_404_NOT_FOUND)
        connections = repository_models.GitRepositoryConnection.objects.filter(code_style=code_style)
        for connection in connections:
            repository_tasks.delete_hook.delay(request.user.username, connection.repository.id)
            connection.delete()
        code_style.delete()
        return Response({'result': id}, status.HTTP_200_OK)
    return Response({'detail': 'You should provide code style id'}, status.HTTP_400_BAD_REQUEST)