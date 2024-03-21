"""
Test the recipe API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    # create and return a recipe detail URL
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    # create and return a sample recipe
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 22,
        'price': Decimal('5.00'),
        'description': 'Sample recipe description',
        'link': 'https://example.com/recipe.pdf',
    }
    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    # create and return a sample user
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    # test unauthenticated recipe API access
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        # test that authentication is required
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    # test authenticated API requests
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        # test retrieving a list of recipes
        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        # test list of recipes is limited to user
        other_user = create_user(
            email='other@example.com', password='password123',)
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        # test get recipe detail
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        # test create recipe
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        # test partial update of a recipe
        original_link = 'https://example.com/original.pdf'
        recipe = create_recipe(
            user=self.user, title='Sample recipe title', link=original_link,)

        payload = {'title': 'New title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        # test full update of a recipe
        recipe = create_recipe(
            user=self.user, title='Sample recipe title',
            link='https://example.com/original.pdf',
            description='Sample recipe description',
        )

        payload = {
            'title': 'New title',
            'time_minutes': 25,
            'price': Decimal('5.00'),
            'link': 'https://example.com/new.pdf',
            'description': 'New description',
        }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        # test update user returns error
        new_user = create_user(email='user2@example.com',
                               password='testpass123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        # test deleting a recipe was successful
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_user_recipe_error(self):
        # test trying to delete other user's recipe returns error
        new_user = create_user(email='user2@example.com',
                               password='testpass123')
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        # test creating a recipe with new tags
        payload = {
            'title': 'Avocado lime cheesecake',
            'time_minutes': 20,
            'price': Decimal('10.00'),
            'tags': [{'name': 'Vegan'}, {'name': 'Dessert'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe.first()
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], user=self.user,).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        # test creating a recipe with existing tags
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('5.00'),
            'tags': [{'name': tag_indian.name}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe.first()
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'], user=self.user,).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        # test creating tag when updating a recipe
        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        # test assigning an exising tag to a recipe
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tags(self):
        # test clearing a recipe tags
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_new_ingredients(self):
        """ test creating a recipe with new ingredients"""
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00'),
            'ingredients': [{'name': 'Chocolate'}, {'name': 'Cheese'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe.first()
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'], user=self.user,).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredients(self):
        """ test creating a new recipe with existing ingredients"""
        ingredient = Ingredient.objects.create(
            user=self.user, name='Lemon')

        payload = {
            'title': 'Lemonade',
            'time_minutes': 5,
            'price': Decimal('2.00'),
            'ingredients': [{'name': ingredient.name}, {'name': 'Sugar'}],
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipe.count(), 1)
        recipe = recipe.first()
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'], user=self.user,).exists()
            self.assertTrue(exists)
