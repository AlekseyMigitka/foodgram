from django.contrib import admin

from recipes.models import (
    Recipe,
    Tag,
    Ingredient,
    RecipeIngredient,
    Purchase,
    Favorite,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для модели Tag."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели Ingredient."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


class IngredientAmountInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'pub_date', 'favorites_count')
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'author')
    inlines = (IngredientAmountInline,)

    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'Количество в избранном'


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Админка для модели Purchase."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для модели Favorite."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')
