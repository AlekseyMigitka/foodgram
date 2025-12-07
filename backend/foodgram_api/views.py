from djoser.views import UserViewSet as DjoserUserViewSet
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated,
)
from rest_framework.response import Response

from foodgram_api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    SetPasswordSerializer,
    TagSerializer,
    UserSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    SubscriptionSerializer,
    ShortRecipeSerializer,
)
from foodgram_api.filters import RecipeFilter, IngredientFilter
from foodgram_api.permissions import IsAuthorOrReadOnly
from recipes.models import (
    Ingredient, Tag, Recipe, Purchase, Favorite
)
from users.models import User, Subscription


class UserViewSet(DjoserUserViewSet):
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def get_permissions(self):
        if self.action in ["avatar", "set_password", "me"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Возвращает данные текущего пользователя."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="set_password"
    )
    def set_password(self, request):
        """Смена пароля текущего пользователя."""
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["put", "delete"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="me/avatar"
    )
    def avatar(self, request):
        user = request.user

        if request.method == "PUT":
            if 'avatar' not in request.data:
                return Response(
                    {"avatar": ["Обязательное поле."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if user.avatar:
            user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="subscriptions"
    )
    def subscriptions(self, request):
        user = request.user
        authors = User.objects.filter(following__user=user)

        page = self.paginate_queryset(authors)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="subscribe"
    )
    def subscribe(self, request, id=None):
        user = request.user
        try:
            author = User.objects.get(id=id)
        except User.DoesNotExist:
            return Response({"detail": "Автор не найден"}, status=404)

        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=400
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Подписка уже существует"},
                    status=400
                )

            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author,
                context={"request": request}
            )
            return Response(serializer.data, status=201)

        deleted = Subscription.objects.filter(
            user=user,
            author=author
        ).delete()
        if deleted[0] == 0:
            return Response({"errors": "Подписка не существует"}, status=400)

        return Response(status=204)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None

    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeReadSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filterset_class = RecipeFilter
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted_count = Favorite.objects.filter(
            user=user,
            recipe=recipe
        ).delete()[0]
        if deleted_count == 0:
            return Response(
                {"errors": "Рецепт не в избранном"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Purchase.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Purchase.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(
                recipe,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            purchase = Purchase.objects.filter(user=user, recipe=recipe)
            if purchase.exists():
                purchase.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                {"errors": "Рецепт не в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок пользователя."""
        user = request.user
        purchases = Purchase.objects.filter(user=user).select_related('recipe')

        if not purchases.exists():
            return Response(
                {"error": "Список покупок пуст"},
                status=status.HTTP_400_BAD_REQUEST
            )

        ingredients_totals = {}

        for purchase in purchases:
            recipe = purchase.recipe
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient_name = recipe_ingredient.ingredient.name
                if ingredient_name in ingredients_totals:
                    ingredients_totals[ingredient_name]["amount"] += (
                        recipe_ingredient.amount
                    )
                else:
                    ingredients_totals[ingredient_name] = {
                        "amount": recipe_ingredient.amount,
                        "measurement_unit":
                            recipe_ingredient.ingredient.measurement_unit
                    }

        lines = ["Список покупок:\n"]
        for ingredient_name, data in ingredients_totals.items():
            lines.append(
                f"- {ingredient_name} — {data['amount']}"
                f"{data['measurement_unit']}"
            )

        response_text = "\n".join(lines)
        response = HttpResponse(response_text, content_type='text/plain')
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        url_name='get-link'
    )
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""

        base_url = "http://127.0.0.1:8000/api/recipes"
        short_link = f"{base_url}/{pk}/"

        return Response(
            {"short-link": short_link},
            status=status.HTTP_200_OK
        )
