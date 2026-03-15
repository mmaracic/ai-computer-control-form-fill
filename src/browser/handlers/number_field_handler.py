"""Handler for numeric input fields."""

from src.browser.handlers.fillable_field_handler import FillableFieldHandler
from src.browser.models import FieldType


class NumberFieldHandler(FillableFieldHandler):
    """Detects and fills HTML number inputs (input[type='number'])."""

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.NUMBER

    @property
    def _css_selector(self) -> str:
        """CSS selector matching number input elements."""
        return "input[type='number']"
