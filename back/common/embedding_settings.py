import json
from typing import Any

from pydantic import BaseModel, ValidationInfo, field_validator


# Helper function for the conversion logic to keep the class DRY
def _convert_dict_input_to_hashable_tuple(
    v: Any, field_name: str,
) -> tuple[tuple[str, Any], ...]:
    """
    Converts a dictionary input (from JSON string, dict, or list/tuple of pairs)
    into a sorted tuple of (key, value) items for hashability.
    """
    parsed_dict: dict[str, Any]

    if isinstance(v, str):
        try:
            # Attempt to parse the string as JSON
            parsed_dict = json.loads(v)
        except json.JSONDecodeError:
            raise ValueError(
                f"{field_name}: Invalid JSON string provided: '{v}'",
            )
    elif isinstance(v, dict):
        # Input is already a dictionary
        parsed_dict = v
    elif isinstance(v, (list, tuple)) and all(
        isinstance(item, tuple) and len(item) == 2 for item in v
    ):
        # Input is already a list/tuple of (key, value) pairs.
        # Ensure keys are strings (common for JSON and consistency) and then sort.
        return tuple(sorted(map(lambda x: (str(x[0]), x[1]), v)))
    else:
        # Input is not a recognizable format
        raise ValueError(
            f"{field_name} must be a JSON string representing a dictionary, "
            f"a Python dictionary, or a list/tuple of 2-element (key, value) "
            f"tuples. Received: {type(v)}",
        )

    if not isinstance(parsed_dict, dict):
        # This check is mostly a safeguard if json.loads somehow returns non-dict
        raise ValueError(
            f"{field_name}: Parsed value from string is not a dictionary. "
            f"Received: {type(parsed_dict)}",
        )

    # Convert dictionary to a sorted tuple of (key, value) items
    # Sorting by key ensures consistent order for hashing
    return tuple(sorted(parsed_dict.items()))


class EmbeddingSettings(BaseModel, frozen=True):
    litellm_model: str
    # The fields will store the kwargs as hashable tuples of (key, value) pairs
    litellm_query_kwargs: tuple[tuple[str, Any], ...]
    litellm_document_kwargs: tuple[tuple[str, Any], ...]

    @field_validator(
        "litellm_query_kwargs",
        "litellm_document_kwargs",
        mode="before",  # Validate before Pydantic's standard type checking for these fields
    )
    @classmethod
    def _validate_and_prepare_kwargs(
        cls, v: Any, info: ValidationInfo,
    ) -> tuple[tuple[str, Any], ...]:
        """
        Validates and converts input for kwarg fields (litellm_query_kwargs,
        litellm_document_kwargs) to a hashable tuple format.
        The `info.field_name` is used for more specific error messages.
        """
        return _convert_dict_input_to_hashable_tuple(v, field_name=info.field_name)

    # Optional: Properties to easily get these back as dictionaries when needed
    @property
    def query_kwargs_as_dict(self) -> dict[str, Any]:
        """Returns litellm_query_kwargs as a standard dictionary."""
        return dict(self.litellm_query_kwargs)

    @property
    def document_kwargs_as_dict(self) -> dict[str, Any]:
        """Returns litellm_document_kwargs as a standard dictionary."""
        return dict(self.litellm_document_kwargs)
