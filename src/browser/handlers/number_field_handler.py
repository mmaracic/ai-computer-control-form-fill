"""Handler for numeric input fields."""

from src.browser.handlers.fillable_field_handler import FillableFieldHandler
from src.browser.handlers.form_field_handler import AriaRole
from src.browser.models import FieldType


class NumberFieldHandler(FillableFieldHandler):
    """Detects and fills HTML number inputs (input[type='number'])."""

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.NUMBER

    @property
    def _aria_role(self) -> AriaRole | None:
        """Return the ARIA role for number inputs."""
        return "spinbutton"

    @property
    def _css_selector(self) -> str:
        """CSS selector matching number input elements."""
        return "input[type='number']"
