"""Handler for email input fields."""

from src.browser.handlers.fillable_field_handler import FillableFieldHandler
from src.browser.models import FieldType


class EmailFieldHandler(FillableFieldHandler):
    """Detects and fills HTML email inputs (input[type='email'])."""

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.EMAIL

    @property
    def _css_selector(self) -> str:
        """CSS selector matching email input elements."""
        return "input[type='email']"
