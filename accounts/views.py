from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth import login,logout,authenticate
from django.conf.urls.static import static

# Create your views here.
def signup_user(request):
    if request.method=="POST":
        first_name=request.POST.get("first_name")
        last_name=request.POST.get("last_name")
        username=request.POST.get("username")
        email=request.POST.get("email")
        first_name=request.POST.get("first_name")
        password=request.POST.get("password")
        confirm_password=request.POST.get("password2")
        if password==confirm_password:
            if User.objects.filter(username=username).exists():
                error="Username Already exists"
                return render(request,"register.html",{"error":error})    
            elif User.objects.filter(email=email).exists():
                error="Email Already exists"
                return render(request,"register.html",{"error":error})
            else:
                user=User.objects.create_user(first_name=first_name,last_name=last_name,email=email,password=password,username=username)
                user.save()
                return redirect("login_user")
        else:
            error="Password doesn't match"
            return render(request,"register.html",{"error":error})
    else:
        return render(request,"register.html")


def login_user(request):
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect("/")
        else:
            error="Incorrect email or password"
            print(user)
            return render(request,"login.html",{"error":error})
    else:
        return render(request,"login.html")

def logout_user(request):
    logout(request)
    return redirect(to="/")
