"""dla_olka_1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.contrib import admin
from Core import views as core_views
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()

urlpatterns = router.urls

urlpatterns += [
    path('admin/', admin.site.urls),
    path('image/upload', core_views.ImageUpload.as_view(), name='image_upload'),
    path('api/token/', core_views.TokenLoginView.as_view(), name='token_login'),
    path('link/original/', core_views.OriginalLink.as_view(), name='original_link'),
    path('image/list', core_views.ImageList.as_view(), name='image_list'),
    path('link/expiring/generate', core_views.GenerateExpiringLink.as_view(), name='generate_expiring_link'),
    path('link/expiring/get', core_views.ExpiringLink.as_view(), name='get_expiring_link'),
    path('link/res/first', core_views.ResolutionPicture.as_view(), name='resolution-picture')
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)