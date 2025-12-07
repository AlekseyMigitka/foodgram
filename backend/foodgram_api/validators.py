import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext


class ForbiddenSymbolsPasswordValidator:
    """
    Валидатор запрещает использование некоторых символов в пароле.
    Например: пробел, кавычки, обратный слэш и т.п.
    """

    forbidden_chars = r'[\'\"\s\\/]'

    def validate(self, password, user=None):
        if re.search(self.forbidden_chars, password):
            raise ValidationError(
                gettext(
                    "Пароль содержит недопустимые символы"
                ),
                code='invalid_characters'
            )

    def get_help_text(self):
        return gettext(
            "Ваш пароль не должен содержать пробелы, кавычки, / или \\."
        )
