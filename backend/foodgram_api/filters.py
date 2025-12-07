from django_filters.rest_framework import FilterSet, filters
from recipes.models import Recipe, Tag, Ingredient


class RecipeFilter(FilterSet):
    author = filters.AllValuesMultipleFilter(
        field_name='author__id',
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset

        if value:
            return queryset.filter(purchased_by__user=user)
        else:
            return queryset.exclude(purchased_by__user=user)


class IngredientFilter(FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
