# Serializers for recipe APIs
from rest_framework import serializers
from core.models import Recipe, Tag


class RecipeSerializer(serializers.ModelSerializer):
    # serializer for recipes
    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializer):
    # serializer for recipe detail view
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']
        read_only_fields = RecipeSerializer.Meta.read_only_fields


class TagSerializer(serializers.ModelSerializer):
    # serializer for tag objects
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
