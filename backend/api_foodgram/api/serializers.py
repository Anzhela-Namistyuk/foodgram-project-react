import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from django.db import transaction
from rest_framework import serializers
from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):

        user = self.context['request'].user
        return (user.is_authenticated
                and obj.subscription_author.filter(
                    subscriber=user).exists())

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'id',
            'username',
            'is_subscribed'
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    subscriber = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    author = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Subscription
        fields = ('subscriber', 'author')

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('subscriber', 'author'),
                message='Вы уже подписаны на автора'
            )
        ]

    def validate(self, data):
        request = self.context['request']
        subscriber = request.user
        author_id = request.parser_context['kwargs']['user_id']
        if subscriber.id == int(author_id):
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя')
        return data


class RecipesForActionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('name', 'image', 'id', 'cooking_time')


class AuthorSubscriptionSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        recipes_limit = self.context.get(
            'recipes_limit'
        )
        recipes = obj.recipes.all()[:recipes_limit]
        return RecipesForActionsSerializer(
            recipes, many=True).data

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (user.is_authenticated
                and obj.subscription_author.filter(
                    subscriber=user).exists())

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'recipes',
            'recipes_count',
            'is_subscribed'
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class FavoriteSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = Favorite
        fields = ('recipe', 'user')

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('recipe', 'user'),
                message='Рецепт уже добавлен в список избранных'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all()
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )

    class Meta:
        model = ShoppingCart
        fields = ('recipe', 'user')

        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('recipe', 'user'),
                message='Рецепт уже добавлен в список покупок'
            )
        ]


class IngredientRecipeSerializer(serializers.ModelSerializer):
    name = serializers.StringRelatedField(
        source='ingredient.name',
    )
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit',
    )
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientRecipe
        fields = ('name', 'measurement_unit', 'id', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer()
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField()
    is_in_shopping_cart = serializers.BooleanField()

    def get_ingredients(self, obj):
        return IngredientRecipeSerializer(
            IngredientRecipe.objects.filter(recipe=obj).all(),
            many=True).data

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time')


class AddIngredientForRecipeSerializer(serializers.ModelSerializer):
    recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(write_only=True,
                                      validators=[MinValueValidator(1)])

    class Meta:
        model = IngredientRecipe
        fields = ('recipe', 'id', 'amount')


class Base64ImageFile(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            end_img, image = data.split(';base64,')
            extension = end_img.split('/')[-1]
            data = ContentFile(base64.b64decode(image),
                               name='photo.' + extension)
        return super().to_internal_value(data)


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    ingredients = AddIngredientForRecipeSerializer(
        many=True, source='ingredientrecipe_set'
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageFile()
    author = CustomUserSerializer(required=False)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredientrecipe_set')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        create_ingredients = [
            IngredientRecipe(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount'])
            for ingredient in ingredients]
        IngredientRecipe.objects.bulk_create(
            create_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop(
            'ingredientrecipe_set', None)
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
            create_ingredients = [
                IngredientRecipe(
                    recipe=instance,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount'])
                for ingredient in ingredients]

            IngredientRecipe.objects.bulk_create(
                create_ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, obj):
        self.fields.pop('ingredients')
        self.fields['tags'] = TagSerializer(many=True)
        representation = super().to_representation(obj)
        representation['ingredients'] = IngredientRecipeSerializer(
            IngredientRecipe.objects.filter(
                recipe=obj).all(), many=True).data

        representation['is_favorited'] = Favorite.objects.filter(
            user__id=obj.author.id, recipe__pk=obj.id).exists()
        representation['is_in_shopping_cart'] = ShoppingCart.objects.filter(
            user__id=obj.author.id, recipe__pk=obj.id).exists()
        return representation

    def validate_tags(self, data):
        if not data:
            raise serializers.ValidationError('Выберите тег/теги')
        return data

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError('Выберите ингредиент')
        return data
