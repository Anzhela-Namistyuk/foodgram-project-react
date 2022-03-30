from django.contrib.auth import get_user_model
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscription
from .pagination import CustomPageNumberPagination
from .permissions import ReadAndOwner
from .serializers import (AuthorSubscriptionSerializer,
                          CreateUpdateRecipeSerializer, CustomUserSerializer,
                          FavoriteSerializer, IngredientSerializer,
                          RecipeListSerializer, RecipesForActionsSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          TagSerializer)

User = get_user_model()


class CreateDeleteViewSet(mixins.CreateModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    pass


class UserCreateListRetrieve(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPageNumberPagination

    def list(self, request, *args, **kwargs):
        return Response(self.get_serializer(
            self.queryset, many=True).data)

    @action(detail=False, methods=['get'])
    def get_user(self, request, user_id=None, *args, **kwargs):
        if user_id == 'me':
            return self.me(request, *args, **kwargs)
        user = get_object_or_404(User, pk=user_id)
        return Response(self.get_serializer(user).data)


class SubscriptionViewSet(CreateDeleteViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated, ]

    def create(self, request, *args, **kwargs):
        subscriber_id = request.user.id
        author_id = kwargs.get('user_id')
        author = get_object_or_404(User, id=author_id)
        data = {'subscriber': subscriber_id, 'author': author_id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(AuthorSubscriptionSerializer(
            author, context={'request': request}).data,
            status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        author_id = kwargs.get('user_id')
        subscriber_id = request.user.id
        get_object_or_404(User, id=author_id)
        subscription = Subscription.objects.filter(
            subscriber__id=subscriber_id, author__id=author_id)
        if subscription.exists():
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Такой подписки не существует'},
                        status=status.HTTP_400_BAD_REQUEST)


class SubscriptionsViewSet(mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    serializer_class = AuthorSubscriptionSerializer
    pagination_class = CustomPageNumberPagination
    permission_classes = [permissions.IsAuthenticated, ]

    def get_queryset(self):
        qs = Subscription.objects.filter(subscriber=self.request.user)
        return User.objects.filter(subscription_author__in=qs)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny, ]


class FavoriteViewSet(CreateDeleteViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    pagination_class = None
    permission_classes = [permissions.IsAuthenticated, ]

    def create(self, request, *args, **kwargs):
        user = request.user
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        data = {'user': user.id, 'recipe': recipe_id}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecipesForActionsSerializer(
            recipe, context={'request': request}).data,
            status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        user = request.user
        recipe_id = self.kwargs.get('recipe_id')
        get_object_or_404(Recipe, id=recipe_id)
        favorite = Favorite.objects.filter(
            user__id=user.id, recipe__id=recipe_id)
        if favorite.exists():
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Такой подписки не существует'},
                        status=status.HTTP_400_BAD_REQUEST)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny, ]

    def get_queryset(self):
        ingredients = Ingredient.objects
        name = self.request.query_params.get('name')
        if name:
            ingredients = ingredients.filter(name__istartswith=name)
        return ingredients.all()


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [ReadAndOwner, ]
    pagination_class = CustomPageNumberPagination

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CreateUpdateRecipeSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        tags = self.request.query_params.getlist('tags')
        user = self.request.user
        author = self.request.query_params.get('author', None)
        queryset = Recipe.objects
        if author:
            queryset = queryset.filter(author=author)
        if tags:
            queryset = queryset.filter_by_tags(tags)

        queryset = queryset.add_user_annotations(user.pk)
        if self.request.query_params.get('is_favorited'):
            queryset = queryset.filter(is_favorited=True)
        if self.request.query_params.get('is_in_shopping_cart'):
            queryset = queryset.filter(is_in_shopping_cart=True)
        return queryset


class ShoppingCartApiView(APIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        user = request.user
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        data = {'user': user.id, 'recipe': recipe_id}
        serializer = ShoppingCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RecipesForActionsSerializer(
            recipe, context={'request': request}).data,
            status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        user = request.user
        recipe_id = self.kwargs.get('recipe_id')
        get_object_or_404(Recipe, id=recipe_id)
        recipe_in_shopping_cart = ShoppingCart.objects.filter(
            recipe__id=recipe_id, user__id=user.id)
        if recipe_in_shopping_cart.exists():
            recipe_in_shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Такого рецепта нет в списке покупок'},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def download_shopping_cart(request):
    query = IngredientRecipe.objects.select_related(
        'recipe', 'ingredient'
    )
    query = query.filter(
        recipe__shopping_carts__user=request.user
    )
    query = query.values(
        'ingredient__name', 'ingredient__measurement_unit'
    ).annotate(
        name=F('ingredient__name'),
        unit=F('ingredient__measurement_unit'),
        total=Sum('amount')
    ).order_by('-total')

    text = '\n'.join([f"{el['name']} ({el['unit']}) - {el['total']}"
                      for el in query])
    filename = 'shopping_cart.txt'
    response = HttpResponse(text, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response
