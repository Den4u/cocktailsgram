import django_filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    """Ингредиент-фильтр."""

    search_param = 'name'


class RecipeFilter(django_filters.FilterSet):
    """Рецепт-фильтр."""

    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug')
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart')
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited')

    class Meta:
        model = Recipe
        fields = ('author', 'tags',)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value == 1 and not user.is_anonymous:
            return queryset.filter(cart__user=user)
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value == 1 and not user.is_anonymous:
            return queryset.filter(favorites__user=user)
        return queryset
