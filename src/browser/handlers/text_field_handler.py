"""Handler for plain text input fields."""

from src.browser.handlers.fillable_field_handler import FillableFieldHandler
from src.browser.handlers.form_field_handler import AriaRole
from src.browser.models import FieldType


class TextFieldHandler(FillableFieldHandler):
    """Detects and fills HTML text inputs (input[type='text'])."""

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.TEXT

    @property
    def _aria_role(self) -> AriaRole | None:
        """Return the ARIA role for plain text inputs."""
        return "textbox"

    @property
    def _css_selector(self) -> str:
        """CSS selector matching plain text input elements."""
        return "input[type='text']"
