from django.urls import path
from . import views

urlpatterns = [
    path('home', views.home, name='home' ),
    path('login', views.loginUser, name='login'),
    path('register', views.registerUser, name='register'),
    path('logout', views.logoutUser, name='logout'),

]
