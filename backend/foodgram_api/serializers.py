from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (
    Ingredient, Tag, RecipeIngredient, Recipe,
)
from users.models import User, Subscription


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели User."""

    password = serializers.CharField(write_only=True)
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "password",
            "avatar",
        )
        extra_kwargs = {"password": {"write_only": True},
                        "email": {"required": True}}

    def create(self, validated_data):
        """Создание пользователя."""
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def get_is_subscribed(self, obj):
        """Проверка подписки на автора."""
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return request.user.follower.filter(author=obj).exists()

    def validate_password(self, value):
        """Валидация пароля."""
        validate_password(value)
        return value

    def validate_email(self, value):
        """Валидация email."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Пользователь с таким email уже существует."
            )
        return value


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля текущего пользователя."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        """Проверяет, что текущий пароль введён верно."""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль.")
        return value

    def validate_new_password(self, value):
        """Валидация нового пароля."""
        from django.contrib.auth.password_validation import validate_password
        validate_password(value)
        return value

    def save(self, **kwargs):
        """Меняет пароль пользователя."""
        user = self.context["request"].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return user


class SubscriptionSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context["request"]
        limit = request.query_params.get("recipes_limit")

        qs = obj.recipes.all()
        if limit and limit.isdigit():
            qs = qs[:int(limit)]

        return ShortRecipeSerializer(
            qs,
            many=True,
            context={"request": request}
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления или удаления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def validate_avatar(self, image):
        if image.content_type not in ["image/jpeg", "image/png"]:
            raise serializers.ValidationError("Разрешены только JPG и PNG.")
        return image


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Tag."""

    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ingredient."""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientAmountSerializer(serializers.Serializer):
    """Сериализатор для количества ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(min_value=1)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_image(self, obj):
        """Получение изображения."""
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return ''

    def get_is_favorited(self, obj):
        """Проверка, добавлен ли рецепт в избранное текущего пользователя."""
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return request.user.favorites.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка, добавлен ли рецепт в список покупок пользователя."""
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return request.user.purchases.filter(recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = IngredientAmountSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'cooking_time',
            'ingredients',
            'tags',
        )

    def validate(self, attrs):
        errors = {}

        ingredients = attrs.get('ingredients') or []
        if not ingredients:
            errors['ingredients'] = 'Нужен хотя бы один ингредиент.'
        else:
            seen = set()
            for item in ingredients:
                ingredient_obj = item.get('id')
                amount = item.get('amount')
                if ingredient_obj is None or amount is None:
                    errors['ingredients'] = (
                        'Каждый ингредиент должен содержать id и amount.'
                    )
                    break
                try:
                    ingredient_id = (
                        ingredient_obj.id if hasattr(ingredient_obj, 'id')
                        else int(ingredient_obj)
                    )
                except Exception:
                    errors['ingredients'] = 'Неверный id ингредиента.'
                    break
                if ingredient_id in seen:
                    errors['ingredients'] = (
                        'Ингредиенты не должны дублироваться.'
                    )
                    break
                seen.add(ingredient_id)
                if amount <= 0:
                    errors['ingredients'] = (
                        'Количество ингредиента должно быть положительным.'
                    )
                    break

        tags = attrs.get('tags') or []
        if not tags:
            errors['tags'] = 'Нужен хотя бы один тег.'
        else:
            try:
                tag_ids = [t.id if hasattr(t, 'id') else int(t) for t in tags]
            except Exception:
                errors['tags'] = 'Неверный идентификатор тега.'
            else:
                if len(tag_ids) != len(set(tag_ids)):
                    errors['tags'] = (
                        'Теги не должны дублироваться.'
                    )

        cooking_time = attrs.get('cooking_time')
        if cooking_time is None or cooking_time <= 0:
            errors['cooking_time'] = 'Время готовки должно быть больше нуля.'

        if 'image' in attrs and attrs.get('image') in (None, ''):
            errors['image'] = 'Поле image не может быть пустым.'

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        author = self.context['request'].user

        with transaction.atomic():
            recipe = Recipe.objects.create(author=author, **validated_data)
            recipe.tags.set(tags)

            recipe_ingredients = []
            for item in ingredients_data:
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient=item['id'],
                        amount=item['amount']
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        with transaction.atomic():
            instance.save()

            if ingredients_data is not None:
                instance.recipe_ingredients.all().delete()
                recipe_ingredients = []
                for item in ingredients_data:
                    recipe_ingredients.append(
                        RecipeIngredient(
                            recipe=instance,
                            ingredient=item['id'],
                            amount=item['amount']
                        )
                    )
                RecipeIngredient.objects.bulk_create(recipe_ingredients)

            if tags is not None:
                instance.tags.set(tags)

        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context=self.context
        ).data


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецептов."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj):
        """Получение изображения."""
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return ''
