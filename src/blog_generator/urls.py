
from django.urls import path
from . import views 

urlpatterns = [
    path("", views.index, name='index'),
    path("login", views.login, name='login'),
    path("register", views.register, name='register'),
    path("logout", views.logout, name='logout'),
    path("generate-blog", views.generate_blog, name='generate-blog'),
    path("all-blogs", views.all_blogs, name= "all-blogs"),
    path("blog-details/<int:id>", views.blog_details, name="blog-details")

]
