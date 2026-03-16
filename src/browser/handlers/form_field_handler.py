"""Abstract base class for form field detection and interaction handlers."""

from abc import ABC, abstractmethod
from typing import Literal

from playwright.async_api import Locator, Page

from src.browser.models import FieldType, FormField

LOCATOR_TIMEOUT_MS: int = 3000
AriaRole = Literal["button", "checkbox", "combobox", "radio", "spinbutton", "textbox"]


class FormFieldHandler(ABC):
    """Interface for detecting and filling a specific type of form field.

    Each concrete handler is responsible for one FieldType: it knows how to
    find fields of that type on a page and how to interact with them.
    """

    @property
    @abstractmethod
    def field_type(self) -> FieldType:
        """The FieldType this handler is responsible for."""

    @property
    def _aria_role(self) -> AriaRole | None:
        """The ARIA role used for label-based locator resolution. None if not applicable."""
        return None

    @abstractmethod
    async def find_fields(self, page: Page) -> list[FormField]:
        """Evaluate the page and return all fields matching this handler's type.

        Args:
            page: The Playwright Page to evaluate.

        Returns:
            List of FormField models for fields of this handler's type.

        """

    @abstractmethod
    async def fill(self, locator: Locator, value: str) -> None:
        """Interact with the located element to apply the given value.

        Args:
            locator: Playwright Locator pointing to the target element.
            value: The value to apply (text, option text, 'true'/'false', etc.).

        """

    def get_locator(
        self, container: Page | Locator, form_field: FormField, identifier: str
    ) -> Locator:
        """Build a Playwright Locator from the FormField's identifying attributes.

        Prefers field_id, then name, then ARIA role with label, then label, then placeholder.
        The container can be a Page or a scoped Locator (e.g. a modal dialog).

        Args:
            container: The Playwright Page or scoped Locator to build the locator against.
            form_field: The FormField whose attributes are used to construct the locator.
            identifier: The original identifier string, used only in the error message.

        Returns:
            A Playwright Locator for the field.

        Raises:
            ValueError: If the FormField has no usable locator attributes.

        """
        if form_field.field_id:
            return container.locator(f"#{form_field.field_id}")
        if form_field.name:
            return container.locator(f'[name="{form_field.name}"]')
        role = self._aria_role
        if role and form_field.label:
            return container.get_by_role(role, name=form_field.label, exact=True)
        if form_field.label:
            return container.get_by_label(form_field.label, exact=True)
        if form_field.placeholder:
            return container.get_by_placeholder(form_field.placeholder, exact=True)
        msg = f"Field '{identifier}' has no usable locator attributes."
        raise ValueError(msg)
