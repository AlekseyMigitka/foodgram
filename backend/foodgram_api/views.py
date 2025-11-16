from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from djoser.views import UserViewSet as DjoserUserViewSet

from users.models import User
from foodgram_api.serializers import (
    UserSerializer, AvatarSerializer, SetPasswordSerializer)


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
