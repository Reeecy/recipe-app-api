# Views from the user API
from django.shortcuts import render
from rest_framework import generics
from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""
    serializer_class = UserSerializer
