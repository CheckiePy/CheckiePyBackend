"""acs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^update/', views.update_repository),
    url(r'^list/', views.repository_list),
    url(r'^last_update/', views.last_repository_update),
    url(r'^connect/', views.connect_repository),
    url(r'^handle_hook/(?P<id>[0-9]+)/', views.handle_hook),
    url(r'^disconnect/', views.disconnect_repository),
]
