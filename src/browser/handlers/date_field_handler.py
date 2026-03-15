"""Handler for date input fields."""

from src.browser.handlers.fillable_field_handler import FillableFieldHandler
from src.browser.models import FieldType


class DateFieldHandler(FillableFieldHandler):
    """Detects and fills HTML date inputs (input[type='date'])."""

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.DATE

    @property
    def _css_selector(self) -> str:
        """CSS selector matching date input elements."""
        return "input[type='date']"
