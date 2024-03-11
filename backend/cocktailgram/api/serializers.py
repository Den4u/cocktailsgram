from djoser.serializers import UserSerializer
from django.core.validators import MinValueValidator
from rest_framework import serializers

from .fields import Base64ImageField
from recipes.models import (Recipe, Tag, Ingredient, RecipeIngredient,
                            RecipeInFavorite, RecipeInShoppingCart)
from users.models import User, Subscribe


class UserSerializer(UserSerializer):
    """Сериализатор пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.following.filter(user=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов при получении рецепта."""

    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class IngredientCreateInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор добавления ингредиентов при создании рецепта."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания/изменения рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientCreateInRecipeSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'image',
            'name',
            'text',
            'cooking_time')

    def add_ingredients(self, recipe, ingredients):
        ing_data = [RecipeIngredient(
            recipe=recipe,
            amount=ingredient['amount'],
            ingredient_id=ingredient['id']
        ) for ingredient in ingredients]
        return RecipeIngredient.objects.bulk_create(ing_data)

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.add_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.set(tags)
        ingredients = validated_data.pop('ingredients')
        instance.ingredients.clear()
        self.add_ingredients(instance, ingredients)
        instance = super().update(instance, validated_data)
        return instance

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeListSerializer(instance, context=context).data

    def validate_ingredients(self, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            if ingredient['id'] in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты не могут повторяться!')
            ingredients_list.append(ingredient['id'])
            if int(ingredient['amount']) < 1:
                raise serializers.ValidationError(
                    'Минимальное количество ингредиента - 1!')
        if not ingredients:
            raise serializers.ValidationError('Пустое поле c ингредиентами!')
        return ingredients

    def validate_tags(self, tags):
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError('Теги не могут повторяться!')
            tags_list.append(tag)
        if not tags:
            raise serializers.ValidationError('Пустое поле c тегом!')
        return tags

    def validate_image(self, image):
        if not image:
            raise serializers.ValidationError('Добавьте изображение!')
        return image


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор отображения рецепта."""

    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredient')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time')

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.favorites.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.cart.filter(user=request.user).exists()


class RecipeInSubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор отображения рецепта при подписке."""

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time')


class SubscribeSerializer(UserSerializer):
    """Сериализатор подписки."""

    id = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField(read_only=True)
    recipes = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes_count',
            'recipes')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return obj.following.filter(user=request.user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        limit = self.context.get('request').GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeInSubscribeSerializer(recipes, many=True).data


class SubscribeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки."""

    class Meta:
        model = Subscribe
        fields = '__all__'
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=('user', 'author'),
                message='Повторная подписка невозможна!'
            ), )

    def validate_author(self, value):
        if value == self.context['request'].user:
            raise serializers.ValidationError(
                'Увы, нельзя подписаться на самого себя!')
        return value

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return SubscribeSerializer(instance.author, context=context).data


class RecipeInFavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор добавления в избранное."""

    class Meta:
        model = RecipeInFavorite
        fields = '__all__'
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=RecipeInFavorite.objects.all(),
                fields=('user', 'recipe'),
                message='Повторное добавление в избранное невозможно!'
            ), )

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeInSubscribeSerializer(
            instance.recipe, context=context).data


class RecipeInShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор добавления в корзину."""

    class Meta:
        model = RecipeInShoppingCart
        fields = '__all__'
        validators = (
            serializers.UniqueTogetherValidator(
                queryset=RecipeInShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Повторное добавление в корзину невозможно!'
            ), )

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return RecipeInSubscribeSerializer(
            instance.recipe, context=context).data
