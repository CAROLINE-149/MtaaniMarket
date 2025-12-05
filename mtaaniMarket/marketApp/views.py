from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .forms import SignupForm
from .models import Profile
from .decorators import role_required


def registerUser(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            #create a profile with the selected role
            role = form.cleaned_data['role']
            Profile.objects.create(user=user, role=role)  

            if role not in ['buyer', 'seller']:
                form.add_error('role', 'Invalid role')
                return render(request, 'marketApp/register_form.html', {'form': form})
            
            user.save()
            
            login(request, user)
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'marketApp/register_form.html', {'form': form})

def home(request):
    context ={}
    return render(request,'marketApp/home.html',context)

def loginUser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # check role
            role = user.profile.role

            if role == 'buyer':
                return redirect('buyer_home')   # URL name for buyer home
            else:
                return redirect('seller_home')  # URL name for seller home

        else:
            return render(request, 'marketApp/login_form.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'marketApp/login_form.html')

def logoutUser(request):
    context ={}
    logout(request)
    return redirect('home')


def about(request):
    context ={}
    return render(request,'marketApp/about.html',context)

def shop(request):
    context ={}
    return render(request,'marketApp/shop.html',context)

def buyer_home(request):
    context ={}
    return render(request,'marketApp/buyer_home.html',context)

def seller_home(request):
    context ={}
    return render(request,'marketApp/seller_home.html',context)

@role_required(allowed_roles=['buyer'])
def buyer_home(request):
    return render(request, 'marketApp/buyer_home.html')

@role_required(allowed_roles=['seller'])
def seller_home(request):
    return render(request, 'marketApp/seller_home.html')