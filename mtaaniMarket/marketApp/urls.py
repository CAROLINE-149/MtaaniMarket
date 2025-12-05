from django.urls import path
from . import views

urlpatterns = [
    path('home', views.home, name='home' ),
    path('login', views.loginUser, name='login'),
    path('register', views.registerUser, name='register'),
    path('logout', views.logoutUser, name='logout'),
    path('about', views.about, name='about'),
    path('shop', views.shop, name='shop'),
    path('buyer/home', views.buyer_home, name='buyer_home'),
    path('seller/home', views.seller_home, name='seller_home'),

]
