from django.contrib import admin

from .models import (Favorite, Ingredient, IngredientRecipe, Recipe,
                     ShoppingCart, Tag)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_author', 'count_in_favorite')
    list_filter = ('name', 'author__username', 'tags')

    def count_in_favorite(self, obj):
        return obj.favorite.count()

    def get_author(self, obj):
        return obj.author.username

    count_in_favorite.short_description = "in_favorite(count)"
    get_author.short_description = "author"


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
admin.site.register(IngredientRecipe)
admin.site.register(Tag)
