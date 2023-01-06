"""
byceps.services.metrics.models
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Label:
    name: str
    value: str

    def serialize(self) -> str:
        escaped_value = _escape_label_value(self.value)
        return f'{self.name}="{escaped_value}"'


def _escape_label_value(value: str) -> str:
    def escape(char):
        if char == '\\':
            return r'\\'
        elif char == '"':
            return r'\"'
        elif char == '\n':
            return r'\n'
        else:
            return char

    return ''.join(map(escape, value))


@dataclass(frozen=True)
class Metric:
    name: str
    value: float
    labels: list[Label] = field(default_factory=list)

    def serialize(self) -> str:
        labels_str = ''
        if self.labels:
            labels_str = (
                '{'
                + ', '.join(label.serialize() for label in self.labels)
                + '}'
            )

        return f'{self.name}{labels_str} {self.value}'
