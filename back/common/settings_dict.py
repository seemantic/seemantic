import json
from typing import Annotated, Any

from pydantic import BeforeValidator, ValidationInfo

# Define the target hashable dictionary representation
type SettingsDictEntry = tuple[str, Any]
# This is the target format: a sorted tuple of (key, value) tuples
type _SettingsDict = tuple[SettingsDictEntry, ...]

# --- Helper functions (can remain as they encapsulate the core logic) ---

def _is_settings_dict_entry(
    v: Any) -> bool:  # noqa: ANN401
    if isinstance(v, tuple):
        v_tuple: tuple[Any, ...] = v
        return len(v_tuple) == 2 and isinstance(v_tuple[0], str)
    return False

def _is_settings_dict(
    v: Any) -> bool:  # noqa: ANN401
    if isinstance(v, tuple):
        v_tuple: tuple[Any, ...] = v
        return all(
            _is_settings_dict_entry(item) for item in v_tuple
        )
    return False

# --- Reusable Pydantic V2 Validator Function ---

def _settings_dict_validator(v: Any, info: ValidationInfo) -> _SettingsDict:  # noqa: ANN401
    """
    Pydantic V2 validator function that calls the core conversion logic.
    Used with Annotated and BeforeValidator.
    """
    parsed_dict: dict[str, Any]

    if isinstance(v, str):
        parsed_dict = json.loads(v)
    elif isinstance(v, dict):
        parsed_dict = v
    elif _is_settings_dict(v):
        return v
    else:
        # Input is not a recognizable format
        raise ValueError(
            f"{info.field_name} must be a JSON string representing a dictionary, "
            f"a Python dictionary, or a list/tuple of 2-element (key, value) "
            f"tuples. Received: {type(v)}",
        )
    # Convert dictionary to a sorted tuple of (key, value) items
    # Sorting by key ensures consistent order for hashing
    settings: tuple[tuple[str, Any], ...] = tuple(sorted(parsed_dict.items()))
    return settings


# --- Define the Reusable Annotated Type Alias ---

# Use Annotated to combine the target type (SettingsDict) with a BeforeValidator
# The BeforeValidator runs _settings_dict_validator *before* Pydantic's
# standard validation for SettingsDict (tuple[tuple[str, Any], ...]).
type SettingsDict = Annotated[_SettingsDict, BeforeValidator(_settings_dict_validator)]
