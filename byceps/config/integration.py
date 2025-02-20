"""
byceps.config.integration
~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2025 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import json
import os
from pathlib import Path
from typing import Any

import rtoml
import structlog

from byceps.byceps_app import BycepsApp
from byceps.util.result import Err, Ok

from .converter import convert_config
from .errors import ConfigurationError
from .parser import parse_config


log = structlog.get_logger()


def init_app(app: BycepsApp) -> None:
    if app.byceps_app_mode.is_site():
        if not app.config.get('SITE_ID'):
            raise ConfigurationError('No site ID configured.')


def parse_value_from_environment(
    key: str,
) -> bool | dict | float | int | list | str | None:
    value = os.environ.get(key)
    if value is None:
        return None

    try:
        # Detect booleans, numbers, collections, `null`/`None`.
        return json.loads(value)
    except Exception:
        # Leave it as a string.
        return value


def read_configuration_from_file_given_in_env_var() -> dict[str, Any]:
    """Load configuration from file specified via environment variable."""
    filename_str = os.environ.get('BYCEPS_CONFIG_FILE')
    if filename_str:
        filename = Path(filename_str)
        return _read_modern_configuration_from_file(filename)
    else:
        filename_str = os.environ.get('BYCEPS_CONFIG')
        if not filename_str:
            return {}

        filename = Path(filename_str)
        return _read_configuration_from_file(filename)


def _read_configuration_from_file(filename: Path) -> dict[str, Any]:
    """Load configuration from file."""
    try:
        with filename.open() as f:
            return rtoml.load(f)
    except OSError as e:
        e.strerror = f'Unable to load configuration file ({e.strerror})'
        raise


def _read_modern_configuration_from_file(filename: Path) -> dict[str, Any]:
    """Load modern configuration from file."""
    match parse_config(filename.read_text()):
        case Ok(config):
            return convert_config(config)
        case Err(errors):
            log.error(
                'Could not parse configuration file.',
                filename=filename,
                errors=errors,
            )
            raise ConfigurationError('Errors found in configuration file')
