"""Playwright browser service for managing a single browser page session."""

import logging

from playwright.async_api import Browser, Locator, Page, Playwright, async_playwright

logger = logging.getLogger(__name__)

NOT_STARTED_ERROR: str = "BrowserService has not been started. Call start() first."


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
        """Close the open page, the browser, and stop Playwright."""
        if self._page is not None and not self._page.is_closed():
            await self._page.close()
        self._page = None
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
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

    async def close_page(self) -> None:
        """Close and discard the current browser page."""
        if self._page is not None and not self._page.is_closed():
            await self._page.close()
            logger.info("Browser page closed.")
        self._page = None


async def find_first_matching_locator(locators: list[Locator]) -> Locator | None:
    """Return the `.first` sub-locator of the first locator that matches elements.

    Iterates through locators in order, skipping any that raise a Playwright
    error or match zero elements.

    Args:
        locators: Ordered list of Playwright Locator objects to try.

    Returns:
        The `.first` locator of the first match, or None if none matched.

    """
    for locator in locators:
        try:
            count = await locator.count()
            if count > 0:
                return locator.first
        except Exception as exc:
            logger.debug("Locator check failed: %s", exc)
    return None
