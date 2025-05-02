from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import blogPost, User

from django.conf import settings
import os

from dotenv import load_dotenv
load_dotenv()

import json
import markdown2

from pytubefix import YouTube
from pytubefix.cli import on_progress

# from pytube import YouTube
import assemblyai as aai

from google import genai


def yt_title(link):
    yt = YouTube(link)
    return yt.title
    
def download_audio(link):
    yt = YouTube(link, on_progress_callback= on_progress)
    video = yt.streams.filter(only_audio=True).first()
    if video is None:
        return "[Error] No audio stream found."
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file 

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = os.getenv("ASSEMBLYAI_API")
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
    transcript = aai.Transcriber(config=config).transcribe(audio_file)
    if transcript.status == "error":
        raise RuntimeError(f"Transcription failed: {transcript.error}")
    return transcript.text


def generate_blog_from_ai(content):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=["summarize text, write it like an article and blog for linkedin, don't make look like an youtube video and make the langauge easy", content],


    )
    return response.text


# Create your views here.

@login_required
def index(request):
    if request.user.is_authenticated:
        return render(request, 'blog_generator/index.html')
    else:
        return render(request, 'blog_generator/login.html')


def all_blogs(request):
    blog_articles = blogPost.objects.filter(user=request.user)
    return render(request, "blog_generator/all-blogs.html", {"blog_articles": blog_articles})
      
def blog_details(request, id):
    blog_article_detail = blogPost.objects.get(id=id)
    if request.user == blog_article_detail.user:
        return render(request, "blog_generator/blog-details.html", {"blog_article_detail": blog_article_detail})
    else:
        return redirect('/blog_generator')
        
    
    

 
@csrf_exempt 
def generate_blog(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            yt_link = data.get('link', '').strip()
            if not yt_link.startswith("http"):
                return JsonResponse({'error': 'Invalid YouTube link'}, status=400)
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'invalid data method'},status=400)
        
    
        #get yt title 
        title = yt_title(yt_link)
        
        #Get transcription
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "failed to get transcript"}, status=500)
        
        #get the content of the blogifiy transicript
        blog_content = generate_blog_from_ai(transcription)
        if not blog_content:
            return JsonResponse({'error': "failed to generate blog article"}, status=500)
        
        #save the blog article
        the_new_blogPost = blogPost.objects.create(
            user= request.user,
            youtube_title = title,
            youtube_link = yt_link,
            generated_content = markdown2.markdown(blog_content.strip())
        )
        
        the_new_blogPost.save()
        
        
        
        #return the blog article as a response 
        return  JsonResponse({'content': blog_content})
            
        
    
    
    else:
        return JsonResponse({'error': 'invalid request method'},status=405)


    
def login(request):
    if request.method == 'POST':
        username= request.POST.get('username')
        password= request.POST.get('password')
        user = auth.authenticate(request, username=username, password=password )
        if user is not None:
            auth.login(request, user=user)
            message = "You have logged in successfully."
            return render(request, 'blog_generator/index.html', {"message":message})
        else:
            error_message = "You have made a mistake in your password or username, please try again."
            return render(request, 'blog_generator/login.html', {"error_message": error_message})
        
    else:  
        return render(request, 'blog_generator/login.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password") 
        
        if password == confirm_password:
            user = User(username=username, email=email, password=password)
            user.save()
            message = messages.success(request,"You have been created your account successfully, login now")
            return render(request, 'blog_generator/login.html', {"message": message})
        else:
            username = request.POST.get("username")
            email = request.POST.get("email")
            error_message ="You have made mistake in your password, please try again."
            return render(request, 'blog_generator/register.html', {"error_message": error_message,
                                                                    "username":username,
                                                                    "email":email
                                                                    })


    else:
            
        return render(request, 'blog_generator/register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')