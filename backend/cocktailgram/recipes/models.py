from django.db import models
from django.core.validators import MinValueValidator

from users.models import User


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField('Название', max_length=256)
    measurement_unit = models.CharField('Единица измерения', max_length=100)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name', )
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='unique_name_measurement_unit'
            )
        ]

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField('Название', max_length=100, unique=True)
    slug = models.SlugField('Идентификатор', unique=True)
    color = models.CharField('Цветовой код', max_length=7, unique=True,)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='recipes')
    name = models.CharField('Название', max_length=200)
    image = models.ImageField('Изображение', upload_to='images/')
    text = models.TextField('Описание', max_length=500)
    ingredients = models.ManyToManyField(Ingredient,
                                         verbose_name='Ингредиенты',
                                         related_name='recipes',
                                         through='RecipeIngredient')
    tags = models.ManyToManyField(Tag,
                                  verbose_name='Теги',
                                  related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        default=1,
        validators=[MinValueValidator(1)])
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )

    def __str__(self):
        return f'{self.name} - {self.author}'


class RecipeIngredient(models.Model):
    """Промежуточная таблица ингредиента и рецепта."""

    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт',
                               related_name='recipe_ingredient')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   verbose_name='Ингредиент',
                                   related_name='recipe_ingredient')
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[MinValueValidator(1)])

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_recipe_ingredient'
            )
        ]


class RecipeInShoppingCart(models.Model):
    user = models.ForeignKey(User,
                             verbose_name='Пользователь',
                             on_delete=models.CASCADE,
                             related_name='cart')
    recipe = models.ForeignKey(Recipe,
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE,
                               related_name='cart')

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_cart'
            ),
        )

    def __str__(self):
        return f'{self.recipe} в корзине у {self.user} .'


class RecipeInFavorite(models.Model):
    """Модель избранного."""

    user = models.ForeignKey(User,
                             verbose_name='Пользователь',
                             on_delete=models.CASCADE,
                             related_name='favorites')
    recipe = models.ForeignKey(Recipe,
                               verbose_name='Рецепт',
                               on_delete=models.CASCADE,
                               related_name='favorites',)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_favorite'
            ),
        )

    def __str__(self):
        return f'{self.recipe} в избранном у {self.user}.'
