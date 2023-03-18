from PIL import Image as pil
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
from rest_framework import status
from django.contrib.auth import authenticate
from django.contrib.auth.views import LoginView
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from .models import Tier, Image, Token
from django.http import FileResponse, JsonResponse
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
            return JsonResponse({'token': token.key}, status = status.HTTP_200_OK)
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=status.HTTP_404_NOT_FOUND)

@method_decorator(csrf_exempt, name='dispatch')
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

    def post(self, request):
        token_key = request.GET.get('token')
        try:
            token = Token.objects.get(key=token_key)
        except:
            return JsonResponse({"result": "error",
                    "message": "Wrong identifiacation token, use login view to recieve proper token"}, status= 400)
        user = User.objects.get(token=token)
        if token:
            title = request.GET.get('title')
            image_file = request.data["image"]
            filename= image_file.name
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in ["jpg","png"]:
                Image.objects.create(image=image_file, user=user, title=title)
            else:
                return JsonResponse({"result": "error","message": "Wrong file extension, should be either png or jpg"}, status= 400)
            return JsonResponse({"result": "success","message": "Image uploaded"}, status= 200)
        else:
            return JsonResponse({"result": "error","message": "Json decoding error"}, status= 400)

class ImageList(views.APIView):
    def get(self, request):
        token_key = request.GET.get('token')
        try:
            token = Token.objects.get(key=token_key)
        except:
            return JsonResponse({"result": "error",
                    "message": "Wrong identifiacation token, use login view to recieve proper token"}, status= 400)
        user = User.objects.get(token=token)
        images = Image.objects.filter(user=user)
        response = {"result":"list"}
        for image in images:
            response[image.title] = image.id
        return JsonResponse(response, status=200)

class OriginalLink(views.APIView):
    def get(self, request):
        token_key = request.GET.get('token')
        try:
            token = Token.objects.get(key=token_key)
        except:
            return JsonResponse({"result": "error",
                    "message": "Wrong identifiacation token, use login view to recieve proper token"}, status= 400)
        user = User.objects.get(token=token)
        tier = Tier.objects.get(users=user)
        if tier.original_link:
            image_token = request.GET.get('image')
            try:
                image = Image.objects.get(id=image_token)
            except:
                return JsonResponse({"result": "error","message": "Wrong image id, use list enpoint to get proper id"}, status= 400)
            site_domain = request.get_host()
            image_url = image.image.url
            return JsonResponse({"result":"success", "link" : f'{site_domain}{image_url}'}, status=200)
        else:
            return JsonResponse({"result": "error","message": "Service not availabe for your tier"}, status= 400)

class ResolutionPicture(views.APIView):
    def get(self, request):
        token_key = request.GET.get('token')
        try:
            token = Token.objects.get(key=token_key)
        except:
            return JsonResponse({"result": "error",
                    "message": "Wrong identifiacation token, use login view to recieve proper token"}, status= 400)
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
        try:
            image = Image.objects.get(id=image_token)
        except:
            return JsonResponse({"result": "error","message": "Wrong image id, use list enpoint to get proper id"}, status= 400)
        image_path = os.path.join(settings.MEDIA_ROOT, image.image.name.split("/")[-1])
        try:
            with pil.open(image_path) as img:
                width, old_height = img.size
                new_width = (width * height) // old_height
                new_size = (int(new_width), int(height))
                resized_img = img.resize(new_size)
                new_image_path = os.path.join(settings.MEDIA_ROOT, f"{user.id}_{res}_resized_image.jpg")
                resized_img.save(new_image_path, 'JPEG')
        except:
            return JsonResponse({"result": "error","message": "Could not open file"}, status = 400)
        site_domain = request.get_host()
        return JsonResponse({'url': f'{site_domain}/media/{user.id}_{res}_resized_image.jpg'})

class GenerateExpiringLink(views.APIView):
    def get(self, request):
        token_key = request.GET.get('token')
        try:
            token = Token.objects.get(key=token_key)
        except:
            return JsonResponse({"result": "error",
                    "message": "Wrong identifiacation token, use login view to recieve proper token"}, status= 400)
        user = User.objects.get(token=token)
        tier = Tier.objects.get(users=user)
        if tier.expiring_link:
            expiration_time = request.GET.get('expires', '')
            try:
                expiration_time = max(min(int(expiration_time), 30000), 300)
            except:
                return JsonResponse({"result": "error","message": "Expiration time should be a number of seconds without non-numeric characters"}, status= 400)
            image_token = request.GET.get('image')
            try:
                image = Image.objects.get(id=image_token)
            except:
                return JsonResponse({"result": "error","message": "Wrong image id, use list enpoint to get proper id"}, status= 400)
            image_url = os.path.normpath(os.path.join(settings.MEDIA_ROOT, image.image.name))
            serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
            expiration_datetime = datetime.utcnow() + timedelta(seconds=expiration_time)
            expiration_timestamp = int(expiration_datetime.timestamp())
            signed_expiration = serializer.dumps(f"?expires={expiration_timestamp}", salt=settings.SECRET_KEY)
            signed_image_url = serializer.dumps(f"?id={image_url}", salt=settings.SECRET_KEY)
            link = request.get_host() + reverse('get_expiring_link') + f'?expires={signed_expiration}' + f'&id={signed_image_url}'
            return JsonResponse({"result":"success", "link" : f'{link}'}, status = 200)
        else:
            return JsonResponse({"result": "error","message": "Service not availabe for your tier"}, status = 400)

class ExpiringLink(views.APIView):
    def get(self, request):
        signed_expiration_time = request.GET.get('expires', '')
        signed_image_url = request.GET.get('id', '')
        try:
            serializer = URLSafeTimedSerializer(settings.SECRET_KEY)
            image_url = serializer.loads(signed_image_url, salt=settings.SECRET_KEY)
            image_url = image_url.split('id=')[1]
            expiration_time = serializer.loads(signed_expiration_time, salt=settings.SECRET_KEY)
            expiration_time = int(expiration_time.split('expires=')[1])
            
        except SignatureExpired:
            return JsonResponse({"result" : "error", "message" : "The link has expired."}, status = 400)

        except BadSignature:
            return JsonResponse({"result" : "error", "message" : "The link is invalid."}, status = 400)
        
        if int(expiration_time) > int(datetime.utcnow().timestamp()):
            return FileResponse(open(image_url, 'rb'), content_type='image/jpeg')
        elif int(expiration_time) < int(datetime.utcnow().timestamp()):
            return JsonResponse({"result": "error","message": "Link expired"}, status = 400)
        else:
            return JsonResponse({"result": "error","message": "Error unknown"}, status = 400)