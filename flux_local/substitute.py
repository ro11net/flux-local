"""Module for handling postBuild substitution from external sources."""

import logging
from pathlib import Path
from typing import Any

import yaml

from flux_local.exceptions import FluxException

_LOGGER = logging.getLogger(__name__)


class SubstituteException(FluxException):
    """Exception raised when substitution processing fails."""


def load_configmap_data(configmap_path: Path) -> dict[str, str]:
    """
    Load substitution variables from a ConfigMap YAML file.

    Args:
        configmap_path: Path to the ConfigMap YAML file

    Returns:
        Dictionary of variable names to values

    Raises:
        SubstituteException: If the file cannot be read or parsed
    """
    if not configmap_path.exists():
        raise SubstituteException(
            f"ConfigMap file not found: {configmap_path}"
        )

    try:
        with open(configmap_path, "r") as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise SubstituteException(
            f"Failed to parse ConfigMap YAML: {e}"
        ) from e
    except OSError as e:
        raise SubstituteException(
            f"Failed to read ConfigMap file: {e}"
        ) from e

    # Validate it's a ConfigMap
    if not isinstance(content, dict):
        raise SubstituteException(
            f"Invalid ConfigMap format: expected dict, got {type(content)}"
        )

    kind = content.get("kind")
    if kind != "ConfigMap":
        raise SubstituteException(
            f"Invalid resource kind: expected ConfigMap, got {kind}"
        )

    # Extract data section
    data = content.get("data", {})
    if not isinstance(data, dict):
        raise SubstituteException(
            f"Invalid ConfigMap data: expected dict, got {type(data)}"
        )

    # Convert all values to strings
    result = {}
    for key, value in data.items():
        if value is None:
            result[key] = ""
        else:
            result[key] = str(value)

    _LOGGER.debug(
        "Loaded %d substitution variables from %s",
        len(result),
        configmap_path
    )

    return result


def merge_substitutions(
    base_substitutions: dict[str, str],
    global_substitutions: dict[str, str],
) -> dict[str, str]:
    """
    Merge global substitutions with kustomization-specific substitutions.

    Kustomization-specific substitutions take precedence over global ones.

    Args:
        base_substitutions: Substitutions defined in the Kustomization
        global_substitutions: Substitutions from the global ConfigMap

    Returns:
        Merged dictionary with base_substitutions taking precedence
    """
    merged = global_substitutions.copy()
    merged.update(base_substitutions)

    if base_substitutions and global_substitutions:
        overridden = set(base_substitutions.keys()) & set(global_substitutions.keys())
        if overridden:
            _LOGGER.debug(
                "Kustomization overrides %d global substitution(s): %s",
                len(overridden),
                ", ".join(sorted(overridden))
            )

    return merged