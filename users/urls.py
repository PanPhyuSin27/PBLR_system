from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomAuthenticationForm

urlpatterns = [
    path("", views.home_view, name="home"),
    path("projects/", views.projects_view, name="projects"),
    path("recommendations/", views.recommendations_view, name="recommendations"),
    path("recommendations/<int:index>/start/", views.start_recommendation_view, name="start_recommendation"),
    path("showcase/<slug:slug>/start/", views.start_showcase_view, name="start_showcase"),
    path("my-projects/", views.my_projects_view, name="my_projects"),
    path("signup/", views.signup_view, name="signup"),
    path("profile/", views.profile_view, name="profile_view"),
    path("profile/edit/", views.profile_create_or_update, name="profile_edit"),

    path("login/", auth_views.LoginView.as_view(authentication_form=CustomAuthenticationForm), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]