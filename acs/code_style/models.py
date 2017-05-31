from django.db import models
from django.contrib.auth.models import User


class CodeStyle(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=255)
    repository = models.CharField(max_length=255)
    metrics = models.TextField(default='{}')
    calc_status = models.CharField(max_length=32, choices=(('S', 'Started'), ('F', 'Failed'), ('C', 'Completed')),
                                   default='S')
