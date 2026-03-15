"""Handler for button elements (button tag and input[type='button'])."""

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
    "    const text = element.textContent ? element.textContent.trim() : null;"
    "    if (text) return text;"
    "    return element.value || null;"
    "};"
)

_FIND_BUTTON_FIELDS_JS: str = (
    "() => {" + _GET_LABEL_JS + "    const buttons = ["
    '        ...Array.from(document.querySelectorAll("button")), '
    "        ...Array.from(document.querySelectorAll(\"input[type='button']\")), "
    "    ];"
    "    return buttons.map(el => ({"
    "        label: getLabel(el),"
    "        name: el.name || null,"
    "        field_id: el.id || null,"
    "        placeholder: null,"
    "        field_type: 'button',"
    "        current_value: null,"
    "        options: null,"
    "    }));"
    "}"
)


class ButtonFieldHandler(FormFieldHandler):
    """Detects and interacts with HTML button elements.

    Filling a button triggers a click on it, since that is the expected
    interaction associated with button elements.
    """

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.BUTTON

    async def find_fields(self, page: Page) -> list[FormField]:
        """Evaluate the page and return all button fields.

        Args:
            page: The Playwright Page to evaluate.

        Returns:
            List of FormField models for all button elements on the page.

        """
        raw = await page.evaluate(_FIND_BUTTON_FIELDS_JS)
        fields = [FormField.model_validate(f) for f in raw]
        logger.info("Found %d %s field(s)", len(fields), self.field_type.value)
        return fields

    async def fill(self, locator: Locator, value: str) -> None:  # noqa: ARG002
        """Click the button element.

        Args:
            locator: Playwright Locator pointing to the button element.
            value: Unused; clicking is the only meaningful interaction for buttons.

        """
        await locator.click(timeout=LOCATOR_TIMEOUT_MS)
