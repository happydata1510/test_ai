from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),  # 홈 페이지
    path('chat/', views.ChatView.as_view(), name='chat'),  # ChatGPT 서비스 페이지
]
