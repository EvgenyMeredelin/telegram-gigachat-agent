from typing import Any

import black


def format_black(collection: Any) -> str:
    """Наглядное структурированное представление коллекции данных. """
    return black.format_str(repr(collection), mode=black.Mode())
