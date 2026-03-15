"""Handler for textarea fields."""

from src.browser.handlers.fillable_field_handler import FillableFieldHandler
from src.browser.models import FieldType


class TextareaFieldHandler(FillableFieldHandler):
    """Detects and fills HTML textarea elements."""

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.TEXTAREA

    @property
    def _css_selector(self) -> str:
        """CSS selector matching textarea elements."""
        return "textarea"
