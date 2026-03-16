"""Handler for password input fields."""

from src.browser.handlers.fillable_field_handler import FillableFieldHandler
from src.browser.handlers.form_field_handler import AriaRole
from src.browser.models import FieldType


class PasswordFieldHandler(FillableFieldHandler):
    """Detects and fills HTML password inputs (input[type='password'])."""

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.PASSWORD

    @property
    def _aria_role(self) -> AriaRole | None:
        """Return the ARIA role for password inputs."""
        return "textbox"

    @property
    def _css_selector(self) -> str:
        """CSS selector matching password input elements."""
        return "input[type='password']"
