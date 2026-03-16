"""Handler for radio button input fields."""

import logging

from playwright.async_api import Locator, Page

from src.browser.handlers.form_field_handler import (
    AriaRole,
    FormFieldHandler,
    LOCATOR_TIMEOUT_MS,
)
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

_FIND_RADIO_FIELDS_JS: str = (
    "() => {"
    + _GET_LABEL_JS
    + "    const inputs = Array.from(document.querySelectorAll(\"input[type='radio']\"));"
    "    return inputs.map(el => ({"
    "        label: getLabel(el),"
    "        name: el.name || null,"
    "        field_id: el.id || null,"
    "        placeholder: null,"
    "        field_type: 'radio',"
    "        current_value: el.checked ? 'true' : 'false',"
    "        options: null,"
    "    }));"
    "}"
)


class RadioFieldHandler(FormFieldHandler):
    """Detects and fills HTML radio button inputs.

    Filling selects (checks) the radio button regardless of the value passed.
    """

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.RADIO

    @property
    def _aria_role(self) -> AriaRole | None:
        """Return the ARIA role for radio button inputs."""
        return "radio"

    async def find_fields(self, page: Page) -> list[FormField]:
        """Evaluate the page and return all radio button fields.

        Args:
            page: The Playwright Page to evaluate.

        Returns:
            List of FormField models for all radio inputs on the page.

        """
        raw = await page.evaluate(_FIND_RADIO_FIELDS_JS)
        fields = [FormField.model_validate(f) for f in raw]
        logger.info("Found %d %s field(s)", len(fields), self.field_type.value)
        return fields

    async def fill(self, locator: Locator, value: str) -> None:  # noqa: ARG002
        """Check the radio button.

        Args:
            locator: Playwright Locator pointing to the radio input.
            value: Unused; the radio button is always checked when targeted.

        """
        await locator.check(timeout=LOCATOR_TIMEOUT_MS)
