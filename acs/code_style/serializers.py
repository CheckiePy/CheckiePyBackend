from rest_framework import serializers

from . import models


class CodeStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CodeStyle
        fields = ('name', 'repository')
