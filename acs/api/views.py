from django.contrib.auth import logout

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def handle_logout(request):
    request.user.auth_token.delete()
    logout(request)
    return Response({'result': True}, status.HTTP_200_OK)
