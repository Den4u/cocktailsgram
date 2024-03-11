import io

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from rest_framework import viewsets, status
from rest_framework.permissions import (IsAuthenticatedOrReadOnly,
                                        IsAuthenticated)
from rest_framework.decorators import action
from rest_framework.response import Response

from recipes.models import (
    Recipe, Tag, Ingredient, RecipeInFavorite,
    RecipeInShoppingCart, RecipeIngredient)
from users.models import User, Subscribe
from .serializers import (TagSerializer, IngredientSerializer,
                          UserSerializer,
                          RecipeCreateUpdateSerializer,
                          RecipeListSerializer, SubscribeSerializer,
                          SubscribeCreateSerializer,
                          RecipeInFavoriteSerializer,
                          RecipeInShoppingCartSerializer)
from .filters import RecipeFilter, IngredientFilter
from .permissions import IsAuthorOrReadOnlyPermission
from .pagination import PageNumberLimitPagination


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод тега/списка тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Создание/изменение/удаление/вывод рецептов.
       Добавление/удаление - избранное, корзина.
    """

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageNumberLimitPagination
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnlyPermission)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeListSerializer

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='favorite')
    def favorite(self, request, pk):
        if request.method == 'DELETE':
            return self.del_operation(RecipeInFavorite, request.user, pk)
        return self.add_operation(
            RecipeInFavoriteSerializer, request, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart')
    def shopping_cart(self, request, pk):
        if request.method == 'DELETE':
            return self.del_operation(
                RecipeInShoppingCart, request.user, pk)
        return self.add_operation(
            RecipeInShoppingCartSerializer, request, pk)

    def del_operation(self, model, user, pk):
        obj = model.objects.filter(user=user, recipe__id=pk)
        if obj.exists():
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def add_operation(self, serializer, request, pk):
        user = request.user
        serializer = serializer(
            data={'user': user.pk, 'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredient_list = RecipeIngredient.objects.filter(
            recipe__cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit').annotate(amount_sum=Sum('amount'))

        pdfmetrics.registerFont(
            TTFont(
                'Arial',
                'static/ttf_arial/ArialRegular.ttf'))
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont("Arial", 20)
        start_cur = 800
        p.drawString(50, start_cur, 'Shopping list:')
        start_cur = 770
        for ingredient in ingredient_list:
            p.drawString(50, start_cur,
                         f'{ingredient["ingredient__name"]} -'
                         f'{ingredient["amount_sum"]} '
                         f'{ingredient["ingredient__measurement_unit"]}')
            start_cur -= 30
            if start_cur <= 0:
                start_cur = 800
                p.showPage()
                p.setFont("Arial", 20)

        p.showPage()
        p.save()

        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename='shopping_cart.pdf')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вывод игредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientFilter, )
    search_fields = ('^name',)


class UserViewSet(UserViewSet):
    """Пользователь. Создание/удаление/вывод подписок."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageNumberLimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='me')
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe')
    def subscribe(self, request, **kwargs):
        author = get_object_or_404(User, id=self.kwargs.get('id'))
        user = request.user

        if request.method == 'DELETE':
            obj = Subscribe.objects.filter(user=user, author=author)
            if obj.exists():
                obj.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = SubscribeCreateSerializer(
            data={'user': user.pk, 'author': author.pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions')
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)
