from django.db import models
import uuid
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django_extensions.db.models import (
	TimeStampedModel, 
	ActivatorModel,
	TitleDescriptionModel
)


# Create your models here.

image_fs = FileSystemStorage(location='media/', base_url="/media/")

class Token(models.Model):
    key = models.CharField(max_length=40, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

class Model(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    class Meta:
        abstract = True

class Tier(
	TimeStampedModel, 
	ActivatorModel,
	TitleDescriptionModel,
	Model
	):

	class Meta:
		verbose_name_plural = "Tiers"

	users = models.ManyToManyField(User)
	original_link = models.BooleanField()
	expiring_link = models.BooleanField()
	res_1 = models.IntegerField(default=0)
	res_2 = models.IntegerField(default=0)
	res_3 = models.IntegerField(default=0)
	

	def __str__(self):
		return f'{self.title}'
	
class Image(
	TimeStampedModel, 
	ActivatorModel,
	TitleDescriptionModel,
	Model
	):

	class Meta:
		verbose_name_plural = "Images"

	user = models.ForeignKey(User, on_delete = models.CASCADE)
	image = models.ImageField(storage=image_fs)

	def __str__(self):
		return f'{self.title}'