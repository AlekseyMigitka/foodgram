import re

from django.core.exceptions import ValidationError


USERNAME_REGEX = r'^[\w.@+-]+\Z'
USERNAME_INVALID_CHARS_MESSAGE = (
    'Username содержит недопустимые символы: '
    '{invalid_chars}'
)


def validate_username(value):
    """Валидация username: запрещено 'me' и недопустимые символы."""
    if value.lower() == 'me':
        raise ValidationError('Имя пользователя "me" недопустимо.')

    if not re.fullmatch(USERNAME_REGEX, value):
        invalid_chars = sorted(set(re.sub(USERNAME_REGEX, '', value)))
        raise ValidationError(
            USERNAME_INVALID_CHARS_MESSAGE.format(
                invalid_chars=', '.join(invalid_chars)
            )
        )
