from django.contrib import admin

from .models import (
    Tag, Ingredient, Recipe, RecipeInFavorite,
    RecipeInShoppingCart, RecipeIngredient)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    list_filter = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'color',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('author', 'name', 'favorite_count')
    list_filter = ('name', 'author', 'tags',)

    def favorite_count(self, instance):
        return instance.favorites.count()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredient', 'amount')


@admin.register(RecipeInShoppingCart)
class RecipeInShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)


@admin.register(RecipeInFavorite)
class RecipeInFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
