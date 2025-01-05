import operator
from typing import Annotated

import emoji
from pydantic import AfterValidator

OPERATOR_MAPPING = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
}

def demojize_str(text: str) -> str:
    """Convert any unicode emojis to emoji shortcodes"""
    if emoji.emoji_count(text):
        return emoji.demojize(text)
    return text


DemojizedStr = Annotated[str, AfterValidator(demojize_str)]
