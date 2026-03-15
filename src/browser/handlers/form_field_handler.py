"""Abstract base class for form field detection and interaction handlers."""

from abc import ABC, abstractmethod

from playwright.async_api import Locator, Page

from src.browser.models import FieldType, FormField

LOCATOR_TIMEOUT_MS: int = 3000


class FormFieldHandler(ABC):
    """Interface for detecting and filling a specific type of form field.

    Each concrete handler is responsible for one FieldType: it knows how to
    find fields of that type on a page and how to interact with them.
    """

    @property
    @abstractmethod
    def field_type(self) -> FieldType:
        """The FieldType this handler is responsible for."""

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
