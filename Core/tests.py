from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Image, Tier, Token


# Create your tests here.
class MainTest(APITestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.tier = Tier(original_link = True, expiring_link = True)
        self.user = User.objects.create_user(username="test_user", password="8De8XGMndjeUH8T@")
        self.tier.save()
        self.tier.users.add(self.user)
        self.tier.save()
        self.token = Token(key="VbtzLRiClQIYPgj2Q1n8SD7ml74jssFnREOn98xj", user = self.user)
        self.token.save()
        self.image = Image(user=self.user, image="test", title="test_image")
        self.image.save()

    def test_recieve_token(self):
        good_response = self.client.get(reverse("token_login"), {"username" : self.user.username, "password" : "8De8XGMndjeUH8T@"})
        self.assertEqual(good_response.status_code, status.HTTP_200_OK)
        bad_response = self.client.get(reverse("token_login"), {"username" : "usname", "password" : "123"})
        self.assertEqual(bad_response.status_code, status.HTTP_404_NOT_FOUND)

    # def test_image_upload(self):
    #     image_url = os.path.normpath(os.path.join(settings.BASE_DIR, "test_image.jpg"))
    #     img = pil.new(mode="RGB", size=(1, 1), color=(0, 0, 255))
    #     file = BytesIO()
    #     img.save(image_url, 'jpeg')
    #     file.seek(0)
    #     image_url = SimpleUploadedFile(image_url, file.getvalue(), content_type="image/jpeg")
    #     token_key = Token.objects.get(user=self.user).key
    #     good_response = self.client.post(reverse("image_upload"), {"token" : "VbtzLRiClQIYPgj2Q1n8SD7ml74jssFnREOn98xj", "title" : "test_image"}, files={"image" : image_url}, format="multipart")
    #     self.assertEqual(good_response.status_code, status.HTTP_200_OK)

    def test_list(self):
        good_response = self.client.get(reverse("image_list"), {"token" : self.token.key})
        self.assertEqual(good_response.status_code, status.HTTP_200_OK)
        bad_response = self.client.get(reverse("image_list"), {"token" : "Bad"})
        self.assertEqual(bad_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_original(self):
        good_response = self.client.get(reverse("original_link"), {"token" : self.token.key, "image" : self.image.id})
        self.assertEqual(good_response.status_code, status.HTTP_200_OK)
        wrong_token_response = self.client.get(reverse("original_link"), {"token" : "wrong", "image" : self.image.id})
        self.assertEqual(wrong_token_response.status_code, status.HTTP_400_BAD_REQUEST)
        wrong_id_response = self.client.get(reverse("original_link"), {"token" : self.token.key, "image" : "666"})
        self.assertEqual(wrong_id_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_expiring(self):
        good_response = self.client.get(reverse("generate_expiring_link"), {"token" : self.token.key, "image" : self.image.id, "expires" : 3000})
        self.assertEqual(good_response.status_code, status.HTTP_200_OK)
        string_time_response = self.client.get(reverse("generate_expiring_link"), {"token" : self.token.key, "image" : self.image.id, "expires" : "string"})
        self.assertEqual(string_time_response.status_code, status.HTTP_400_BAD_REQUEST)