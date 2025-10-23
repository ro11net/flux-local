"""Tests for substitute module."""

import pytest
from pathlib import Path

from flux_local.substitute import (
    load_configmap_data,
    merge_substitutions,
    SubstituteException,
)


def test_load_configmap_data(tmp_path: Path) -> None:
    """Test loading ConfigMap data."""
    configmap = tmp_path / "config.yaml"
    configmap.write_text("""
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-config
  namespace: default
data:
  KEY1: "value1"
  KEY2: "value2"
  NUMBER_KEY: "123"
""")

    result = load_configmap_data(configmap)

    assert result == {
        "KEY1": "value1",
        "KEY2": "value2",
        "NUMBER_KEY": "123",
    }


def test_load_configmap_not_found(tmp_path: Path) -> None:
    """Test loading non-existent ConfigMap."""
    with pytest.raises(SubstituteException, match="not found"):
        load_configmap_data(tmp_path / "missing.yaml")


def test_load_invalid_yaml(tmp_path: Path) -> None:
    """Test loading invalid YAML."""
    configmap = tmp_path / "invalid.yaml"
    configmap.write_text("{ invalid yaml")

    with pytest.raises(SubstituteException, match="Failed to parse"):
        load_configmap_data(configmap)


def test_load_wrong_kind(tmp_path: Path) -> None:
    """Test loading wrong resource kind."""
    configmap = tmp_path / "secret.yaml"
    configmap.write_text("""
apiVersion: v1
kind: Secret
metadata:
  name: test
data:
  key: value
""")

    with pytest.raises(SubstituteException, match="Invalid resource kind"):
        load_configmap_data(configmap)


def test_merge_substitutions_no_overlap() -> None:
    """Test merging with no overlapping keys."""
    base = {"KEY1": "value1"}
    global_subs = {"KEY2": "value2"}

    result = merge_substitutions(base, global_subs)

    assert result == {"KEY1": "value1", "KEY2": "value2"}


def test_merge_substitutions_with_override() -> None:
    """Test that base substitutions override global ones."""
    base = {"KEY1": "base-value", "KEY2": "value2"}
    global_subs = {"KEY1": "global-value", "KEY3": "value3"}

    result = merge_substitutions(base, global_subs)

    assert result == {
        "KEY1": "base-value",  # Base overrides global
        "KEY2": "value2",
        "KEY3": "value3",
    }


def test_merge_substitutions_empty_base() -> None:
    """Test merging with empty base."""
    result = merge_substitutions({}, {"KEY1": "value1"})
    assert result == {"KEY1": "value1"}


def test_merge_substitutions_empty_global() -> None:
    """Test merging with empty global."""
    result = merge_substitutions({"KEY1": "value1"}, {})
    assert result == {"KEY1": "value1"}
