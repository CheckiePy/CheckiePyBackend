from rest_framework import serializers

from . import models


class CodeStyleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CodeStyle
        fields = ('name', 'repository')


class CodeStyleGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CodeStyle
        fields = ('id', 'name', 'repository')
