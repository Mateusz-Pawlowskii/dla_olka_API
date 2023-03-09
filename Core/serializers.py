from . import models
from rest_framework import serializers
# from rest_framework.fields import CharField, BooleanField


class TierSerializer(serializers.ModelSerializer):

	title = serializers.CharField(required=True)
	description = serializers.CharField(required=True)
	original_link = serializers.BooleanField(required=True)
	expiring_link = serializers.BooleanField(required=True)
	
	
	class Meta:
		model = models.Tier
		fields = (
			'title',
			'description',
			'original_link',
			'expiring_link'
		)
		
class ImageSerializer(serializers.ModelSerializer):

	title = serializers.CharField(required=True)
	description = serializers.CharField(required=True)
	
	
	class Meta:
		model = models.Tier
		fields = (
			'title',
			'description',
		)