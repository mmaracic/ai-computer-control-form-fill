"""Handler for checkbox input fields."""

import logging

from playwright.async_api import Locator, Page

from src.browser.handlers.form_field_handler import FormFieldHandler, LOCATOR_TIMEOUT_MS
from src.browser.models import FieldType, FormField

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

_FIND_CHECKBOX_FIELDS_JS: str = (
    "() => {"
    + _GET_LABEL_JS
    + "    const inputs = Array.from(document.querySelectorAll(\"input[type='checkbox']\"));"
    "    return inputs.map(el => ({"
    "        label: getLabel(el),"
    "        name: el.name || null,"
    "        field_id: el.id || null,"
    "        placeholder: null,"
    "        field_type: 'checkbox',"
    "        current_value: el.checked ? 'true' : 'false',"
    "        options: null,"
    "    }));"
    "}"
)


class CheckboxFieldHandler(FormFieldHandler):
    """Detects and fills HTML checkbox inputs.

    Filling checks the checkbox when value is 'true' (case-insensitive),
    unchecks it otherwise.
    """

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.CHECKBOX

    async def find_fields(self, page: Page) -> list[FormField]:
        """Evaluate the page and return all checkbox fields.

        Args:
            page: The Playwright Page to evaluate.

        Returns:
            List of FormField models for all checkbox inputs on the page.

        """
        raw = await page.evaluate(_FIND_CHECKBOX_FIELDS_JS)
        fields = [FormField.model_validate(f) for f in raw]
        logger.info("Found %d %s field(s)", len(fields), self.field_type.value)
        return fields

    async def fill(self, locator: Locator, value: str) -> None:
        """Check or uncheck the checkbox based on the value.

        Args:
            locator: Playwright Locator pointing to the checkbox input.
            value: Pass 'true' (case-insensitive) to check, anything else to uncheck.

        """
        if value.lower() == "true":
            await locator.check(timeout=LOCATOR_TIMEOUT_MS)
        else:
            await locator.uncheck(timeout=LOCATOR_TIMEOUT_MS)
