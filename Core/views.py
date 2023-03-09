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
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
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
            image_url = image.image.url
            site_domain = request.get_host()
            return JsonResponse({"result":"success", "link" : f'{site_domain}{image_url}'}, status=200)
        else:
            return JsonResponse({"result": "error","message": "Service not availabe for your tier"}, status= 400)

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
            image_url = f'{site_domain}{image.image.url}'
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
            image_url = serializer.dumps(signed_token, salt=expiration_time)

        except SignatureExpired:
            return JsonResponse({"result" : "error", "message" : "The link has expired."}, status = 400)

        except BadSignature:
            return JsonResponse({"result" : "error", "message" : "The link is invalid."}, status = 400)

        return JsonResponse({"result" : "success", "link" : f"{site_domain}{image_url}"}, status = 200)