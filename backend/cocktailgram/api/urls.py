from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import RecipeViewSet, TagViewSet, IngredientViewSet, UserViewSet


router_v1 = DefaultRouter()

router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('recipes', RecipeViewSet, basename='recipes')
router_v1.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router_v1.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
