from django.contrib import admin

from . import models

admin.site.register(models.GitRepository)
admin.site.register(models.GitRepositoryUpdate)
admin.site.register(models.GitRepositoryConnection)