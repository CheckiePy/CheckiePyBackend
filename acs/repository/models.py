from django.db import models
from django.contrib.auth.models import User
from code_style import models as code_style_models


class GitRepository(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=255)
    is_connected = models.BooleanField(default=False)
    code_style_name = models.CharField(max_length=255, default='')

    def __str__(self):
        return '{}. {}'.format(self.id, self.name)


class GitRepositoryUpdate(models.Model):
    user = models.ForeignKey(User)
    datetime = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=32, choices=(('S', 'Started'), ('F', 'Failed'), ('C', 'Completed')),
                              default='S')


class GitRepositoryConnection(models.Model):
    repository = models.ForeignKey(GitRepository)
    code_style = models.ForeignKey(code_style_models.CodeStyle)

    def __str__(self):
        return 'CodeStyle: {} | Repository: {}'.format(self.code_style.id, self.repository.id)
