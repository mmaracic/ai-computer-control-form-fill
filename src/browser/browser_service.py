"""Playwright browser service for managing a single browser page session."""

import logging
from typing import Literal

from playwright.async_api import Browser, Locator, Page, Playwright, async_playwright

from src.browser.handlers.form_field_handler import LOCATOR_TIMEOUT_MS, FormFieldHandler
from src.browser.models import FieldType, FormField, NavigationResult

logger = logging.getLogger(__name__)

NOT_STARTED_ERROR: str = "BrowserService has not been started. Call start() first."
NAVIGATION_WAIT_UNTIL: Literal["domcontentloaded"] = "domcontentloaded"


class BrowserService:
    """Manages Playwright browser lifecycle and a single persistent page session.

    The service must be started with start() before use and stopped with stop()
    during application shutdown.
    """

    _headless: bool
    _handlers: list[FormFieldHandler]
    _handler_map: dict[FieldType, FormFieldHandler]
    _playwright: Playwright | None
    _browser: Browser | None
    _page: Page | None

    def __init__(
        self,
        headless: bool,  # noqa: FBT001
        handlers: list[FormFieldHandler],
    ) -> None:
        """Initialize BrowserService without starting the browser.

        Args:
            headless: Whether to run the browser in headless mode.
            handlers: Ordered list of FormFieldHandler instances used to detect
                and fill form fields. Each handler covers one FieldType.

        """
        self._headless = headless
        self._handlers = handlers
        self._handler_map = {h.field_type: h for h in handlers}
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
        """Run all registered field handlers and return the combined field list.

        Returns:
            List of FormField models discovered by all handlers, in handler order.

        Raises:
            PlaywrightError: If any handler's page evaluation fails.

        """
        page = await self.get_or_create_page()
        fields: list[FormField] = []
        for handler in self._handlers:
            fields.extend(await handler.find_fields(page))
        logger.info("Found %d form field(s) on page.", len(fields))
        return fields

    async def fill_field(self, identifier: str, value: str) -> None:
        """Locate a field by identifier, dispatch to the matching handler, and apply value.

        Calls get_form_fields() to confirm the field exists and determine its type,
        then delegates filling to the handler registered for that FieldType.

        Args:
            identifier: Label text, placeholder, name attribute, or id of the field.
            value: The value to apply (text, option text, 'true'/'false', etc.).

        Raises:
            ValueError: If the field is not found, has no usable locator, or its
                FieldType has no registered handler.
            PlaywrightTimeoutError: If the interaction times out.
            PlaywrightError: If a Playwright error occurs.

        """
        fields = await self.get_form_fields()
        form_field = _find_form_field(fields, identifier)
        if form_field is None:
            msg = f"Field '{identifier}' not found."
            logger.warning("Could not find field with identifier '%s'.", identifier)
            raise ValueError(msg)
        handler = self._handler_map.get(form_field.field_type)
        if handler is None:
            msg = f"No handler registered for field type '{form_field.field_type}'."
            raise ValueError(msg)
        page = await self.get_or_create_page()
        locator = _locator_for_field(page, form_field, identifier)
        await handler.fill(locator.first, value)
        logger.info("Filled field '%s' via %s.", identifier, type(handler).__name__)

    async def click_element(self, identifier: str) -> None:
        """Click a button or interactive element confirmed to exist via get_form_fields().

        Calls get_form_fields() to confirm the element is present on the page,
        then builds a precise locator from the field's attributes and clicks it.

        Args:
            identifier: Label text, placeholder, name attribute, or id of the element.

        Raises:
            ValueError: If the field is not found or has no usable locator attributes.
            PlaywrightTimeoutError: If the click operation times out.
            PlaywrightError: If a Playwright error occurs during the click.

        """
        logger.info("Attempting to click element '%s'.", identifier)
        fields = await self.get_form_fields()
        form_field = _find_form_field(fields, identifier)
        if form_field is None:
            msg = f"Element '{identifier}' not found."
            logger.warning("Could not find element with identifier '%s'.", identifier)
            raise ValueError(msg)
        logger.info("Found element '%s' for clicking.", identifier)
        page = await self.get_or_create_page()
        locator = _locator_for_field(page, form_field, identifier)
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
