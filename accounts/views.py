from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.auth import login,logout,authenticate
from django.conf.urls.static import static

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
