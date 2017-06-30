from rest_framework import serializers

from . import models


class CodeStyleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CodeStyle
        fields = ('name', 'repository')


class CodeStyleReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CodeStyle
        fields = ('id', 'name', 'repository', 'calc_status')


class IdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
