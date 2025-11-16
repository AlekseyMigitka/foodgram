import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ForbiddenSymbolsPasswordValidator:
    """
    Валидатор запрещает использование некоторых символов в пароле.
    Например: пробел, кавычки, обратный слэш и т.п.
    """

    forbidden_chars = r'[\'\"\s\\/]'

    def validate(self, password, user=None):
        if re.search(self.forbidden_chars, password):
            raise ValidationError(
                _("Пароль содержит недопустимые символы: пробел, кавычки, "
                  "/ или \\."),
                code='invalid_characters'
            )

    def get_help_text(self):
        return _(
            "Ваш пароль не должен содержать пробелы, кавычки, / или \\."
        )
