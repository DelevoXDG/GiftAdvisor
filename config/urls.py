"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from core.views import (
    IndexView, 
    extract_metadata, 
    add_gift,
    RecipientsView,
    recipients_list,
    recipient_detail,
    RecipientProfileView,
    search_gifts,
    recent_gifts,
    add_gift_to_recipient,
    gift_detail,
    gift_detail_api,
    PreferencesView,
    update_openai_key
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', IndexView.as_view(), name='index'),
    path('recipients/', RecipientsView.as_view(), name='recipients'),
    path('recipients/<int:recipient_id>/', RecipientProfileView.as_view(), name='recipient_profile'),
    path('gifts/<int:gift_id>/', gift_detail, name='gift_detail'),
    path('preferences/', PreferencesView.as_view(), name='preferences'),
    path('accounts/', include('allauth.urls')),
    
    # API endpoints
    path('api/extract-metadata/', extract_metadata, name='extract_metadata'),
    path('api/gifts/', add_gift, name='add_gift'),
    path('api/gifts/search/', search_gifts, name='search_gifts'),
    path('api/gifts/recent/', recent_gifts, name='recent_gifts'),
    path('api/gifts/<int:gift_id>/', gift_detail_api, name='gift_detail_api'),
    path('api/recipients/', recipients_list, name='recipients_list'),
    path('api/recipients/<int:recipient_id>/', recipient_detail, name='recipient_detail'),
    path('api/recipients/<int:recipient_id>/gifts/', add_gift_to_recipient, name='add_gift_to_recipient'),
    path('api/preferences/openai-key/', update_openai_key, name='update_openai_key'),
]
