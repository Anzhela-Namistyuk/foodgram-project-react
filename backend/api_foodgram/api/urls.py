from api.views import (FavoriteViewSet, IngredientViewSet, RecipeViewSet,
                       ShoppingCartApiView, SubscriptionsViewSet,
                       SubscriptionViewSet, TagViewSet, UserCreateListRetrieve,
                       download_shopping_cart)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

user_pk = UserCreateListRetrieve.as_view(
    {'get': 'get_user', 'post': 'set_password'}
)
subscription = SubscriptionViewSet.as_view(
    {'delete': 'destroy', 'post': 'create'}
)
favorite = FavoriteViewSet.as_view(
    {'delete': 'destroy', 'post': 'create'}
)

router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', UserCreateListRetrieve, basename='users')

urlpatterns = [
    path('users/subscriptions/',
         SubscriptionsViewSet.as_view({'get': 'list'}),
         name='subscriptions'),
    path('users/<user_id>/subscribe/', subscription, name='subscribe'),
    path('recipes/<recipe_id>/favorite/',
         favorite, name='favorite'),
    path('recipes/download_shopping_cart/', download_shopping_cart,
         name='download'),
    path('recipes/<recipe_id>/shopping_cart/', ShoppingCartApiView.as_view(),
         name='shopping_cart'),
    path('users/<pk>/', user_pk, name='get_user_or_set_password'),
    path('', include(router.urls)),
    path(r'auth/', include('djoser.urls.authtoken')),
]
