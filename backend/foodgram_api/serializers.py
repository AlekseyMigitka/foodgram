from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from drf_extra_fields.fields import Base64ImageField

from users.models import User


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
