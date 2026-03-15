"""Handler for select (dropdown) fields."""

import logging

from playwright.async_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

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

_FIND_SELECT_FIELDS_JS: str = (
    "() => {"
    + _GET_LABEL_JS
    + "    const inputs = Array.from(document.querySelectorAll('select'));"
    "    return inputs.map(el => ({"
    "        label: getLabel(el),"
    "        name: el.name || null,"
    "        field_id: el.id || null,"
    "        placeholder: null,"
    "        field_type: 'select',"
    "        current_value: el.options[el.selectedIndex]"
    "            ? el.options[el.selectedIndex].text : null,"
    "        options: Array.from(el.options).map(o => o.text),"
    "    }));"
    "}"
)


class SelectFieldHandler(FormFieldHandler):
    """Detects and fills HTML select (dropdown) elements.

    Detection extracts the available options list from each select element.
    Filling tries to select by visible label first, then by value attribute.
    """

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.SELECT

    async def find_fields(self, page: Page) -> list[FormField]:
        """Evaluate the page and return all select fields with their options.

        Args:
            page: The Playwright Page to evaluate.

        Returns:
            List of FormField models for all select elements on the page.

        """
        raw = await page.evaluate(_FIND_SELECT_FIELDS_JS)
        fields = [FormField.model_validate(f) for f in raw]
        logger.info("Found %d %s field(s)", len(fields), self.field_type.value)
        return fields

    async def fill(self, locator: Locator, value: str) -> None:
        """Select an option in the dropdown, trying by label then by value.

        Args:
            locator: Playwright Locator pointing to the select element.
            value: The visible option text or value attribute to select.

        """
        try:
            await locator.select_option(label=value, timeout=LOCATOR_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            pass
        else:
            return
        await locator.select_option(value=value, timeout=LOCATOR_TIMEOUT_MS)
