"""Factory for creating Playwright-backed agent tools for browser control."""

import json
import logging

from agents import function_tool
from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    Locator,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from src.browser.browser_service import BrowserService, find_first_matching_locator

logger = logging.getLogger(__name__)

NAVIGATION_WAIT_UNTIL = "domcontentloaded"
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


async def _select_from_locator(locator: Locator, value: str) -> bool:
    """Try to select an option in a dropdown by visible label, then by value attribute.

    Args:
        locator: The `.first` Playwright Locator pointing to the select element.
        value: The option text or value to select.

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


def create_browser_tools(
    browser_service: BrowserService,
) -> list:  # noqa: C901, PLR0912, PLR0915
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
        page = await browser_service.get_or_create_page()
        try:
            await page.goto(url, wait_until=NAVIGATION_WAIT_UNTIL)
            title = await page.title()
            current_url = page.url
            logger.info("Navigated to '%s', title: '%s'.", current_url, title)
        except PlaywrightError as exc:
            logger.warning("Navigation to '%s' failed: %s", url, exc)
            return f"Failed to navigate to {url}: {exc}"
        else:
            return f"Navigated to {current_url}. Page title: {title}"

    @function_tool
    async def get_form_fields() -> str:
        """Get all fillable form fields on the current page.

        Returns a JSON array of fields, each with: label, name, field_id,
        placeholder, field_type, current_value, and options (for dropdowns).
        Use this after navigating to a page to discover what fields are available
        and how to identify them for fill_field or select_option.
        """
        page = await browser_service.get_or_create_page()
        try:
            fields = await page.evaluate(GET_FORM_FIELDS_JS)
            logger.info("Found %d form field(s) on page.", len(fields))
        except PlaywrightError as exc:
            logger.warning("Failed to get form fields: %s", exc)
            return f"Failed to retrieve form fields: {exc}"
        else:
            return json.dumps(fields, indent=2)

    @function_tool
    async def fill_field(identifier: str, value: str) -> str:
        """Fill a text, email, number, date, or textarea form field with a value.

        Locates the field by label text, placeholder, name attribute, or id
        (tried in that order). Use get_form_fields first to discover valid identifiers.

        Args:
            identifier: Label text, placeholder, name attribute, or id of the field.
            value: The text value to enter into the field.

        """
        page = await browser_service.get_or_create_page()
        locators = [
            page.get_by_label(identifier, exact=False),
            page.get_by_placeholder(identifier, exact=False),
            page.locator(f'[name="{identifier}"]'),
            page.locator(f"#{identifier}"),
        ]
        match = await find_first_matching_locator(locators)
        if match is None:
            logger.warning("Could not find field with identifier '%s'.", identifier)
            return f"Field '{identifier}' not found. Use get_form_fields to see available fields."
        try:
            await match.fill(value, timeout=LOCATOR_TIMEOUT_MS)
            logger.info("Filled field '%s'.", identifier)
        except PlaywrightTimeoutError:
            return f"Timed out filling field '{identifier}'."
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
        page = await browser_service.get_or_create_page()
        locators = [
            page.get_by_label(identifier, exact=False),
            page.locator(f'[name="{identifier}"]'),
            page.locator(f"#{identifier}"),
        ]
        match = await find_first_matching_locator(locators)
        if match is None:
            return f"Dropdown '{identifier}' not found. Use get_form_fields to see available fields."
        selected = await _select_from_locator(match, value)
        if not selected:
            return f"Option '{value}' not found in dropdown '{identifier}'."
        logger.info("Selected option '%s' in field '%s'.", value, identifier)
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
        page = await browser_service.get_or_create_page()
        locators = [
            page.get_by_role("button", name=identifier),
            page.get_by_role("link", name=identifier),
            page.get_by_label(identifier, exact=False),
            page.get_by_text(identifier, exact=False),
            page.locator(f"#{identifier}"),
        ]
        match = await find_first_matching_locator(locators)
        if match is None:
            return f"Element '{identifier}' not found or not clickable."
        try:
            await match.click(timeout=LOCATOR_TIMEOUT_MS)
            logger.info("Clicked element '%s'.", identifier)
        except PlaywrightTimeoutError:
            return f"Timed out clicking element '{identifier}'."
        except PlaywrightError as exc:
            return f"Error clicking element '{identifier}': {exc}"
        else:
            return f"Clicked '{identifier}'"

    return [navigate, get_form_fields, fill_field, select_option, click_element]
