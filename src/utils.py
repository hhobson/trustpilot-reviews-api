from typing import Annotated

import emoji
from pydantic import AfterValidator


def demojize_str(text: str) -> str:
    """Convert any unicode emojis to emoji shortcodes"""
    if emoji.emoji_count(text):
        return emoji.demojize(text)
    return text


DemojizedStr = Annotated[str, AfterValidator(demojize_str)]
