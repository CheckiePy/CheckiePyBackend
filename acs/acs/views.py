from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework.authtoken.models import Token


@login_required
def login_complete(request):
    token, status = Token.objects.get_or_create(user=request.user)
    return redirect('/login_success/?token={}'.format(token))


def login_success(request):
    return HttpResponse('Success')