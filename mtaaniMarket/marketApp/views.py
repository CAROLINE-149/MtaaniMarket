from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password



# Create your views here.
def home(request):
    context ={}
    return render(request,'marketApp/home.html',context)

def loginUser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        print(password)

        try:
            user = User.objects.get(username=username)
        except:
            print("User does not exists!")
        
        user = authenticate(request, username= username, password = password)

        if user is not None: 
            login(request, user)
            return redirect('')
        else:
            print('Wrong Credentials!!')

    context ={}
    return render(request,'marketApp/login_form.html',context)

def logoutUser(request):
    context ={}
    logout(request)
    return redirect('home')

def registerUser(request):
    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) 
            user.username = f"@{user.username}"
            user.save()
            login(request, user)
            return redirect('')

    context ={"form":form}
    return render(request,'marketApp/register_form.html',context)

def about(request):
    context ={}
    return render(request,'marketApp/about.html',context)

def shop(request):
    context ={}
    return render(request,'marketApp/shop.html',context)
