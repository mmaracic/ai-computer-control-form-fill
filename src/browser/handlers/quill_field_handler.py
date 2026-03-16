"""Handler for Quill rich-text editor fields."""

import logging

from playwright.async_api import Locator, Page

from src.browser.handlers.form_field_handler import LOCATOR_TIMEOUT_MS, FormFieldHandler
from src.browser.models import FieldType, FormField

logger = logging.getLogger(__name__)

_FIND_QUILL_FIELDS_JS: str = (
    "() => {"
    "    const getLabel = (editor) => {"
    "        const ariaLabel = editor.getAttribute('aria-label');"
    "        if (ariaLabel) return ariaLabel;"
    "        const container = editor.closest('.ql-container');"
    "        if (container) {"
    "            const containerAria = container.getAttribute('aria-label');"
    "            if (containerAria) return containerAria;"
    "            if (container.id) {"
    "                const lbl = document.querySelector('label[for=\"' + container.id + '\"]');"
    "                if (lbl) return lbl.textContent.trim();"
    "            }"
    "            let sibling = container.previousElementSibling;"
    "            while (sibling) {"
    "                if (sibling.tagName === 'LABEL') return sibling.textContent.trim();"
    "                sibling = sibling.previousElementSibling;"
    "            }"
    "        }"
    "        return null;"
    "    };"
    "    const editors = Array.from(document.querySelectorAll('div.ql-editor[contenteditable=\"true\"]'));"
    "    return editors.map(el => {"
    "        const container = el.closest('.ql-container');"
    "        return {"
    "            label: getLabel(el),"
    "            name: (container && container.id) ? container.id : null,"
    "            field_id: el.id || null,"
    "            placeholder: el.getAttribute('data-placeholder') || null,"
    "            field_type: 'quill_editor',"
    "            current_value: el.innerText || null,"
    "            options: null,"
    "        };"
    "    });"
    "}"
)

_QUILL_FILL_JS: str = (
    "(el, val) => {"
    "    const container = el.closest('.ql-container');"
    "    if (container && window.Quill) {"
    "        const q = window.Quill.find(container);"
    "        if (q) { q.setText(val); return true; }"
    "    }"
    "    return false;"
    "}"
)


class QuillFieldHandler(FormFieldHandler):
    """Detects and fills Quill rich-text editor instances.

    Discovers editors by querying div.ql-editor[contenteditable='true']. Filling
    first attempts to use the Quill JS API to ensure proper change events are fired;
    falls back to Playwright's native contenteditable fill when the API is unavailable.
    """

    @property
    def field_type(self) -> FieldType:
        """Return the FieldType this handler is responsible for."""
        return FieldType.QUILL_EDITOR

    async def find_fields(self, page: Page) -> list[FormField]:
        """Evaluate the page and return all Quill editor instances.

        Args:
            page: The Playwright Page to evaluate.

        Returns:
            List of FormField models for all Quill editor elements on the page.

        """
        raw = await page.evaluate(_FIND_QUILL_FIELDS_JS)
        fields = [FormField.model_validate(f) for f in raw]
        logger.info("Found %d %s field(s)", len(fields), self.field_type.value)
        return fields

    async def fill(self, locator: Locator, value: str) -> None:
        """Fill the Quill editor with the given text value.

        Tries the Quill JS API first to ensure change events fire correctly;
        falls back to Playwright's native contenteditable fill.

        Args:
            locator: Playwright Locator pointing to the div.ql-editor element.
            value: The plain text value to set in the editor.

        """
        used_api: bool = await locator.evaluate(_QUILL_FILL_JS, value)
        if not used_api:
            await locator.fill(value, timeout=LOCATOR_TIMEOUT_MS)

    def get_locator(
        self, container: Page | Locator, form_field: FormField, identifier: str
    ) -> Locator:  # noqa: ARG002
        """Build a Locator targeting the div.ql-editor element.

        Prefers the editor element's own id, then scopes via the container id,
        then falls back to selecting any visible Quill editor in the container.

        Args:
            container: The Playwright Page or scoped Locator to build the locator against.
            form_field: The FormField whose attributes are used to construct the locator.
            identifier: Unused; present to satisfy the base class interface.

        Returns:
            A Playwright Locator for the Quill editor element.

        """
        if form_field.field_id:
            return container.locator(f"#{form_field.field_id}")
        if form_field.name:
            return container.locator(f"#{form_field.name} div.ql-editor")
        return container.locator("div.ql-editor[contenteditable='true']")
