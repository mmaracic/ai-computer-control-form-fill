"""Factory for creating Playwright-backed agent tools for browser control."""

import json
import logging

from agents import function_tool
from playwright.async_api import Error as PlaywrightError

from src.browser.browser_service import BrowserService

logger = logging.getLogger(__name__)


def create_browser_tools(
    browser_service: BrowserService,
) -> list:
    """Create and return the list of Playwright browser control tools for the agent.

    Args:
        browser_service: The BrowserService instance managing page sessions.

    Returns:
        List of function_tool-decorated async tool functions.

    """

    @function_tool
    async def navigate(url: str) -> str:
        """Navigate the browser to the specified URL.

        Use this tool first to open the target form page before filling any fields.
        Returns the page title on success, or an error message on failure.

        Args:
            url: The full URL to navigate to (e.g. https://example.com/form).

        """
        try:
            result = await browser_service.navigate(url)
        except PlaywrightError as exc:
            logger.warning("Navigation to '%s' failed: %s", url, exc)
            return f"Failed to navigate to {url}: {exc}"
        else:
            return f"Navigated to {result.current_url}. Page title: {result.title}"

    @function_tool
    async def get_form_fields() -> str:
        """Get all fillable form fields on the current page.

        Returns a JSON array of fields, each with: label, name, field_id,
        placeholder, field_type, current_value, and options (for dropdowns).
        Use this after navigating to a page to discover what fields are available
        and how to identify them for fill_field or select_option.
        """
        try:
            fields = await browser_service.get_form_fields()
        except PlaywrightError as exc:
            logger.warning("Failed to get form fields: %s", exc)
            return f"Failed to retrieve form fields: {exc}"
        else:
            return json.dumps([f.model_dump() for f in fields], indent=2)

    @function_tool
    async def fill_field(identifier: str, value: str) -> str:
        """Fill a text, email, number, date, or textarea form field with a value.

        Locates the field by label text, placeholder, name attribute, or id
        (tried in that order). Use get_form_fields first to discover valid identifiers.

        Args:
            identifier: Label text, placeholder, name attribute, or id of the field.
            value: The text value to enter into the field.

        """
        try:
            await browser_service.fill_field(identifier, value)
        except ValueError as exc:
            return f"{exc} Use get_form_fields to see available fields."
        except PlaywrightError as exc:
            return f"Error filling field '{identifier}': {exc}"
        else:
            return f"Filled field '{identifier}' with '{value}'"

    @function_tool
    async def select_option(identifier: str, value: str) -> str:
        """Select an option in a dropdown (select element).

        Locates the dropdown by label text, name attribute, or id. Tries to match
        the option by its visible text first, then by its value attribute.

        Args:
            identifier: Label text, name attribute, or id of the select field.
            value: The visible option text or value attribute to select.

        """
        try:
            await browser_service.fill_field(identifier, value)
        except ValueError as exc:
            return f"{exc} Use get_form_fields to see available fields."
        except PlaywrightError as exc:
            return f"Error selecting option in '{identifier}': {exc}"
        else:
            return f"Selected '{value}' in '{identifier}'"

    @function_tool
    async def click_element(identifier: str) -> str:
        """Click a button, checkbox, radio button, or any interactive element.

        Locates the element by button role name, link role name, aria-label,
        visible text, or id (tried in that order).
        Use this to submit forms by clicking the submit button, or to toggle
        checkboxes and radio buttons.

        Args:
            identifier: Visible text, aria-label, or id of the element to click.

        """
        try:
            await browser_service.click_element(identifier)
        except ValueError as exc:
            return str(exc)
        except PlaywrightError as exc:
            return f"Error clicking element '{identifier}': {exc}"
        else:
            return f"Clicked '{identifier}'"

    return [navigate, get_form_fields, fill_field, select_option, click_element]
