from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from rest_framework.authtoken.models import Token


@login_required
def auth_complete(request):
    token, status = Token.objects.get_or_create(user=request.user)
    return redirect('/?token={}'.format(token))

