"""Pydantic models for browser interaction data structures."""

from enum import Enum

from pydantic import BaseModel


class FieldType(str, Enum):
    """Enumeration of HTML form field input types."""

    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    TEXTAREA = "textarea"
    BUTTON = "button"
    SUBMIT = "submit"
    OTHER = "other"


class FormField(BaseModel):
    """Represents a single form field extracted from a web page."""

    label: str | None
    name: str | None
    field_id: str | None
    placeholder: str | None
    field_type: FieldType
    current_value: str | None
    options: list[str] | None


class NavigationResult(BaseModel):
    """Represents the outcome of a browser navigation action."""

    current_url: str
    title: str
