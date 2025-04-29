from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth

# Create your views here.
def index(request):
    return render(request, 'blog_generator/index.html')

def login(request):
    return render(request, 'blog_generator/login.html' , {})


def register(request):
    return render(request, 'blog_generator/register.html')

def logout(request):
    auth.logout(request)
    redirect('login')