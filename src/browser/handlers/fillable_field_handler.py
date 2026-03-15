"""Abstract base class for input fields that are filled via locator.fill()."""

import logging
from abc import abstractmethod

from playwright.async_api import Locator, Page

from src.browser.handlers.form_field_handler import FormFieldHandler, LOCATOR_TIMEOUT_MS
from src.browser.models import FormField

logger = logging.getLogger(__name__)

_GET_LABEL_JS: str = (
    "const getLabel = (element) => {"
    "    const ariaLabel = element.getAttribute('aria-label');"
    "    if (ariaLabel) return ariaLabel;"
    "    if (element.id) {"
    "        const lbl = document.querySelector('label[for=\"' + element.id + '\"]');"
    "        if (lbl) return lbl.textContent.trim();"
    "    }"
    "    const parent = element.closest('label');"
    "    if (parent) return parent.textContent.replace(element.value, '').trim();"
    "    return null;"
    "};"
)


def _build_find_fields_js(css_selector: str, field_type_value: str) -> str:
    """Build the page-evaluation JS for a text-like input field type.

    Args:
        css_selector: CSS selector string that matches the desired input elements.
        field_type_value: The FieldType enum value string to embed in each result.

    Returns:
        Complete JavaScript function string ready for page.evaluate().

    """
    return (
        "() => {"
        + _GET_LABEL_JS
        + '    const inputs = Array.from(document.querySelectorAll("'
        + css_selector
        + '"));'
        "    return inputs.map(el => ({"
        "        label: getLabel(el),"
        "        name: el.name || null,"
        "        field_id: el.id || null,"
        "        placeholder: el.placeholder || null,"
        "        field_type: '" + field_type_value + "',"
        "        current_value: el.value || null,"
        "        options: null,"
        "    }));"
        "}"
    )


class FillableFieldHandler(FormFieldHandler):
    """Base for input/textarea fields whose value is applied via locator.fill().

    Concrete subclasses declare the CSS selector and FieldType; this class
    provides the shared find_fields() implementation and the fill() behaviour.
    """

    @property
    @abstractmethod
    def _css_selector(self) -> str:
        """CSS selector that matches all elements of this field type."""

    async def find_fields(self, page: Page) -> list[FormField]:
        """Evaluate the page and return all fields matching this handler's CSS selector.

        Args:
            page: The Playwright Page to evaluate.

        Returns:
            List of FormField models for inputs matching this handler's selector.

        """
        js = _build_find_fields_js(self._css_selector, self.field_type.value)
        raw = await page.evaluate(js)
        fields = [FormField.model_validate(f) for f in raw]
        logger.info("Found %d %s field(s)", len(fields), self.field_type.value)
        return fields

    async def fill(self, locator: Locator, value: str) -> None:
        """Fill the element with the given text value.

        Args:
            locator: Playwright Locator pointing to the target input or textarea.
            value: The text value to enter.

        """
        await locator.fill(value, timeout=LOCATOR_TIMEOUT_MS)
