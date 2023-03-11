import time
from PIL import Image as pil
import os
from urllib.parse import urlparse, urlunparse
from django.contrib.auth import authenticate
from django.contrib.auth.views import LoginView
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from .models import Tier, Image, Token
from django.http import JsonResponse
from .serializers import ImageSerializer
from rest_framework import views
from django.utils.crypto import get_random_string
from rest_framework.parsers import MultiPartParser
from django.conf import settings
from itsdangerous import TimestampSigner, URLSafeTimedSerializer, BadSignature, SignatureExpired
from django.urls import reverse


# Create your views here.
class TokenLoginView(LoginView):
    def get(self, request, *args, **kwargs):
        username = request.GET.get('username')
        password = request.GET.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                token = Token.objects.get(user=user)
            except:
                token = Token(user=user, key=get_random_string(length=40))
                token.save()
            return JsonResponse({'token': token.key})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=400)
        
class ImageUpload(views.APIView):
    serializer_class = ImageSerializer
    parser_classes = [MultiPartParser]

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = self.get_serializer_context()
        return self.serializer_class(*args, **kwargs)

    def get(self, request):
        token_key = request.GET.get('token')
        token = Token.objects.get(key=token_key)
        user = User.objects.get(token=token)
        if token:
            title = request.GET.get('title')
            image_file = request.data["image"]
            image = Image.objects.create(image=image_file, user=user, title=title)
            return JsonResponse({"result": "success","message": "Image uploaded"}, status= 200)
        else:
            return JsonResponse({"result": "error","message": "Json decoding error"}, status= 400)

class ImageList(views.APIView):
    def get(self, request):
        token_key = request.GET.get('token')
        token = Token.objects.get(key=token_key)
        user = User.objects.get(token=token)
        images = Image.objects.filter(user=user)
        response = {"result":"list"}
        for image in images:
            response[image.title] = image.id
        return JsonResponse(response, status=200)

class OriginalLink(views.APIView):
    def get(self, request):
        token_key = request.GET.get('token')
        token = Token.objects.get(key=token_key)
        user = User.objects.get(token=token)
        tier = Tier.objects.get(users=user)
        if tier.original_link:
            image_token = request.GET.get('image')
            image = Image.objects.get(id=image_token)
            site_domain = request.get_host()
            image_url = image.image.url
            return JsonResponse({"result":"success", "link" : f'{site_domain}{image_url}'}, status=200)
        else:
            return JsonResponse({"result": "error","message": "Service not availabe for your tier"}, status= 400)

class ResolutionPicture(views.APIView):
    # def generate_presigned_url(self, image_data, height_pixels, image_url, expiration_seconds=3600):
    #     signer = TimestampSigner(settings.SECRET_KEY)
    #     expiration_timestamp = int(time.time()) + expiration_seconds
    #     signed_timestamp = signer.sign(str(expiration_timestamp))

    #     query_params = {'h': str(height_pixels), 'expires': signed_timestamp}
    #     print(query_params)

    #     query_string = ''
    #     for key, value in query_params.items():
    #         query_string += f'{key}={value}&'

    #     query_string = query_string[:-1]
    #     print(query_string)

    #     parsed_url = urlparse(image_url)
    #     new_url_parts = (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, query_string, parsed_url.fragment)
    #     new_url = urlunparse(new_url_parts)

    #     return new_url

    def get(self, request):
        token_key = request.GET.get('token')
        token = Token.objects.get(key=token_key)
        user = User.objects.get(token=token)
        tier = Tier.objects.get(users=user)
        res = request.GET.get('resolution_number')
        if res == "1":
            height = tier.res_1
        elif res == "2":
            height = tier.res_2
        elif res == "3":
            height = tier.res_3
        else:
            return JsonResponse({"result": "error","message": "Wrong resolution number, choose either 1, 2 or 3"}, status = 400)
        image_token = request.GET.get('image')
        image = Image.objects.get(id=image_token)
        image_path = os.path.join(settings.MEDIA_ROOT, image.image.name.split("/")[-1])
        try:
            with pil.open(image_path) as img:
                width, old_height = img.size
                new_width = (width * height) // old_height
                new_size = (int(new_width), int(height))
                resized_img = img.resize(new_size)
                new_image_path = os.path.join(settings.MEDIA_ROOT, "resized_image.jpg")
                resized_img.save(new_image_path, 'JPEG')
        except:
            return JsonResponse({"result": "error","message": "Could not open file"}, status = 400)
        with open(new_image_path, 'rb') as f:
            image_data = f.read()
            image_url = request.build_absolute_uri(image.image.url)
            # new_image_url = self.generate_presigned_url(image_data, height, image_url,)
        site_domain = request.get_host()
        return JsonResponse({'url': f'{site_domain}/media/resized_image.jpg'})

class GenerateExpiringLink(views.APIView):
    def get(self, request):
        token_key = request.GET.get('token')
        token = Token.objects.get(key=token_key)
        user = User.objects.get(token=token)
        tier = Tier.objects.get(users=user)
        if tier.expiring_link:
            expiration_time = request.GET.get('expires', '')
            expiration_time = max(min(int(expiration_time), 30000), 300)
            image_token = request.GET.get('image')
            image = Image.objects.get(id=image_token)
            site_domain = request.get_host()
            image_url = f'{site_domain}/media/{image.image.url}'
            serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
            expiration_datetime = datetime.utcnow() + timedelta(seconds=expiration_time)
            expiration_timestamp = int(expiration_datetime.timestamp())
            signed_url = serializer.dumps(image_url + f"?expires={expiration_timestamp}", salt=settings.SECRET_KEY)
            link = request.get_host() + reverse('get_expiring_link') + f'?token={signed_url}'
            return JsonResponse({"result":"success", "link" : f'{link}'}, status = 200)
        else:
            return JsonResponse({"result": "error","message": "Service not availabe for your tier"}, status = 400)

class ExpiringLink(views.APIView):
    def get(self, request):
        signed_token = request.GET.get('token', '')
        expiration_time = request.GET.get('expires', '')
        site_domain = request.get_host()
        try:
            serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
            image_url = serializer.loads(signed_token, salt=settings.SECRET_KEY)

        except SignatureExpired:
            return JsonResponse({"result" : "error", "message" : "The link has expired."}, status = 400)

        except BadSignature:
            return JsonResponse({"result" : "error", "message" : "The link is invalid."}, status = 400)

        return JsonResponse({"result" : "success", "link" : f"{image_url}"}, status = 200)