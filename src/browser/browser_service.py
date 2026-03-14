"""Playwright browser service for managing a single browser page session."""

import logging
from typing import Literal

from playwright.async_api import Browser, Locator, Page, Playwright, async_playwright
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.browser.models import FormField, NavigationResult

logger = logging.getLogger(__name__)

NOT_STARTED_ERROR: str = "BrowserService has not been started. Call start() first."
NAVIGATION_WAIT_UNTIL: Literal["domcontentloaded"] = "domcontentloaded"
LOCATOR_TIMEOUT_MS: int = 3000

GET_FORM_FIELDS_JS: str = """
() => {
    const getLabel = (element) => {
        const ariaLabel = element.getAttribute('aria-label');
        if (ariaLabel) return ariaLabel;
        if (element.id) {
            const label = document.querySelector(`label[for="${element.id}"]`);
            if (label) return label.textContent.trim();
        }
        const parent = element.closest('label');
        if (parent) return parent.textContent.replace(element.value, '').trim();
        return null;
    };
    const inputs = Array.from(
        document.querySelectorAll('input:not([type="hidden"]), select, textarea')
    );
    return inputs.map(el => ({
        label: getLabel(el),
        name: el.name || null,
        field_id: el.id || null,
        placeholder: el.placeholder || null,
        field_type: el.tagName === 'SELECT'
            ? 'select'
            : el.tagName === 'TEXTAREA'
                ? 'textarea'
                : (el.type || 'text'),
        current_value: el.tagName === 'SELECT'
            ? (el.options[el.selectedIndex] ? el.options[el.selectedIndex].text : null)
            : (el.value || null),
        options: el.tagName === 'SELECT'
            ? Array.from(el.options).map(o => o.text)
            : null,
    }));
}
"""


class BrowserService:
    """Manages Playwright browser lifecycle and a single persistent page session.

    The service must be started with start() before use and stopped with stop()
    during application shutdown.
    """

    _headless: bool
    _playwright: Playwright | None
    _browser: Browser | None
    _page: Page | None

    def __init__(
        self,
        headless: bool,  # noqa: FBT001
    ) -> None:
        """Initialize BrowserService without starting the browser.

        Args:
            headless: Whether to run the browser in headless mode.

        """
        self._headless = headless
        self._playwright = None
        self._browser = None
        self._page = None

    async def start(self) -> None:
        """Start the Playwright instance and launch the Chromium browser."""
        logger.info("Starting Playwright browser (headless=%s).", self._headless)
        playwright = await async_playwright().start()
        self._playwright = playwright
        self._browser = await playwright.chromium.launch(headless=self._headless)
        logger.info("Browser started successfully.")

    async def stop(self) -> None:
        """Close the open page, the browser, and stop Playwright.

        Ignores connection errors that occur when the browser was already closed
        externally (e.g. user closed the headed window before app shutdown).
        """
        if self._page is not None and not self._page.is_closed():
            try:
                await self._page.close()
            except Exception:
                logger.debug("Page already closed before stop().")
        self._page = None
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                logger.debug("Browser already closed before stop().")
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                logger.debug("Playwright already stopped before stop().")
        logger.info("Browser service stopped.")

    async def get_or_create_page(self) -> Page:
        """Return the existing page or create a new one.

        Returns:
            The single persistent Playwright Page for this service.

        Raises:
            RuntimeError: If the service has not been started.

        """
        if self._browser is None:
            msg = NOT_STARTED_ERROR
            raise RuntimeError(msg)
        if self._page is not None and not self._page.is_closed():
            return self._page
        logger.info("Creating new browser page.")
        context = await self._browser.new_context()
        self._page = await context.new_page()
        return self._page

    async def navigate(self, url: str) -> NavigationResult:
        """Navigate the browser to the specified URL.

        Args:
            url: The full URL to navigate to.

        Returns:
            NavigationResult with the resolved URL and page title.

        Raises:
            PlaywrightError: If navigation fails.

        """
        page = await self.get_or_create_page()
        await page.goto(url, wait_until=NAVIGATION_WAIT_UNTIL)
        title = await page.title()
        current_url = page.url
        logger.info("Navigated to '%s', title: '%s'.", current_url, title)
        return NavigationResult(current_url=current_url, title=title)

    async def get_form_fields(self) -> list[FormField]:
        """Evaluate the page to extract all fillable form fields.

        Returns:
            List of FormField models representing each discovered input.

        Raises:
            PlaywrightError: If the page evaluation fails.

        """
        page = await self.get_or_create_page()
        raw_fields = await page.evaluate(GET_FORM_FIELDS_JS)
        fields = [FormField.model_validate(f) for f in raw_fields]
        logger.info("Found %d form field(s) on page.", len(fields))
        return fields

    async def fill_field(self, identifier: str, value: str) -> None:
        """Fill a text, email, number, date, or textarea field by identifier.

        Calls get_form_fields() to confirm the field exists, then builds precise
        locators from the FormField properties (field_id, name, label, placeholder).

        Args:
            identifier: Label text, placeholder, name attribute, or id of the field.
            value: The text value to enter into the field.

        Raises:
            ValueError: If no field matching the identifier is found in the page fields.
            PlaywrightTimeoutError: If the fill operation times out.
            PlaywrightError: If a Playwright error occurs during fill.

        """
        fields = await self.get_form_fields()
        form_field = _find_form_field(fields, identifier)
        if form_field is None:
            msg = f"Field '{identifier}' not found."
            logger.warning("Could not find field with identifier '%s'.", identifier)
            raise ValueError(msg)
        page = await self.get_or_create_page()
        locator = _locator_for_field(page, form_field, identifier)
        await locator.first.fill(value, timeout=LOCATOR_TIMEOUT_MS)
        logger.info("Filled field '%s'.", identifier)

    async def select_option(self, identifier: str, value: str) -> None:
        """Select an option in a dropdown (select element) by identifier.

        Calls get_form_fields() to confirm the field exists and that the requested
        option is available, then builds a precise locator from the FormField properties.

        Args:
            identifier: Label text, name attribute, field_id, or placeholder of the select.
            value: The visible option text to select.

        Raises:
            ValueError: If the dropdown or the requested option is not found.

        """
        fields = await self.get_form_fields()
        form_field = _find_form_field(fields, identifier)
        if form_field is None:
            msg = f"Dropdown '{identifier}' not found."
            raise ValueError(msg)
        if form_field.options is not None and value not in form_field.options:
            msg = f"Option '{value}' not found in dropdown '{identifier}'."
            raise ValueError(msg)
        page = await self.get_or_create_page()
        locator = _locator_for_field(page, form_field, identifier)
        selected = await _select_from_locator(locator.first, value)
        if not selected:
            msg = f"Option '{value}' could not be selected in dropdown '{identifier}'."
            raise ValueError(msg)
        logger.info("Selected option '%s' in field '%s'.", value, identifier)

    async def click_element(self, identifier: str) -> None:
        """Click a button, checkbox, radio button, or any interactive element.

        Locates the element by combining button role, link role, aria-label,
        visible text, and id into a single chained locator.

        Args:
            identifier: Visible text, aria-label, or id of the element to click.

        Raises:
            ValueError: If no clickable element matching the identifier is found.
            PlaywrightTimeoutError: If the click operation times out.
            PlaywrightError: If a Playwright error occurs during the click.

        """
        page = await self.get_or_create_page()
        locator = (
            page.get_by_role("button", name=identifier)
            .or_(page.get_by_role("link", name=identifier))
            .or_(page.get_by_label(identifier, exact=False))
            .or_(page.get_by_text(identifier, exact=False))
            .or_(page.locator(f"#{identifier}"))
        )
        if await locator.count() == 0:
            msg = f"Element '{identifier}' not found or not clickable."
            raise ValueError(msg)
        await locator.first.click(timeout=LOCATOR_TIMEOUT_MS)
        logger.info("Clicked element '%s'.", identifier)

    async def close_page(self) -> None:
        """Close and discard the current browser page."""
        if self._page is not None and not self._page.is_closed():
            await self._page.close()
            logger.info("Browser page closed.")
        self._page = None


def _find_form_field(fields: list[FormField], identifier: str) -> FormField | None:
    """Find a FormField from the list matching identifier against label, name, id, or placeholder.

    Args:
        fields: List of FormField models to search.
        identifier: The label, name, field_id, or placeholder to match.

    Returns:
        The first matching FormField, or None if not found.

    """
    for field in fields:
        if identifier in (field.label, field.name, field.field_id, field.placeholder):
            return field
    return None


def _locator_for_field(page: Page, form_field: FormField, identifier: str) -> Locator:
    """Build a precise Playwright Locator from a FormField's identifying attributes.

    Prefers field_id, then name, then label, then placeholder.

    Args:
        page: The Playwright Page to build the locator against.
        form_field: The FormField whose attributes are used to construct the locator.
        identifier: The original identifier string, used only in the error message.

    Returns:
        A Playwright Locator for the field.

    Raises:
        ValueError: If the FormField has no usable locator attributes.

    """
    if form_field.field_id:
        return page.locator(f"#{form_field.field_id}")
    if form_field.name:
        return page.locator(f'[name="{form_field.name}"]')
    if form_field.label:
        return page.get_by_label(form_field.label, exact=True)
    if form_field.placeholder:
        return page.get_by_placeholder(form_field.placeholder, exact=True)
    msg = f"Field '{identifier}' has no usable locator attributes."
    raise ValueError(msg)


async def _select_from_locator(locator: Locator, value: str) -> bool:
    """Try to select a dropdown option by visible label then by value attribute.

    Args:
        locator: The Playwright Locator pointing to the select element.
        value: The option text or value attribute to select.

    Returns:
        True if the selection succeeded, False otherwise.

    """
    try:
        await locator.select_option(label=value, timeout=LOCATOR_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    else:
        return True
    try:
        await locator.select_option(value=value, timeout=LOCATOR_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    else:
        return True
    return False
