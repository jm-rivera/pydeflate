"""Tests that pydeflate leaves logging configuration to the application."""

import json
import logging
import subprocess
import sys
import textwrap

import pytest

from pydeflate import pydeflate_config

# Runs in a fresh interpreter so nothing imported by the test session hides an
# import-time side effect. Warnings raised from pydeflate's own modules are
# errors, so no import path touches a deprecated name. Third-party warnings
# cannot fail the run.
_IMPORT_PROBE = textwrap.dedent(
    """
    import importlib
    import json
    import logging
    import pkgutil
    import warnings

    warnings.filterwarnings("error", module=r"pydeflate(\\.|$)")

    root = logging.getLogger()
    before = (list(root.handlers), root.level)

    import pydeflate

    for info in pkgutil.walk_packages(pydeflate.__path__, "pydeflate."):
        importlib.import_module(info.name)

    # Created here if no module has asked for it yet, so its state is always checked.
    logging.getLogger("pydeflate")

    loggers = {
        name: {
            "handlers": len(logger.handlers),
            "level": logger.level,
            "propagate": logger.propagate,
        }
        for name, logger in logging.Logger.manager.loggerDict.items()
        if isinstance(logger, logging.Logger)
        and (name == "pydeflate" or name.startswith("pydeflate."))
    }
    print(
        json.dumps(
            {
                "root_unchanged": (list(root.handlers), root.level) == before,
                "loggers": loggers,
            }
        )
    )
    """
)


def test_import_leaves_logging_unconfigured():
    result = subprocess.run(
        [sys.executable, "-c", _IMPORT_PROBE],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    report = json.loads(result.stdout.splitlines()[-1])

    for name, state in report["loggers"].items():
        assert state == {
            "handlers": 0,
            "level": logging.NOTSET,
            "propagate": True,
        }, name
    assert report["root_unchanged"]


@pytest.fixture
def restore_logger():
    """Undo whatever ``setup_logger`` does to the logger it configures."""
    saved = []

    def track(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        saved.append((logger, list(logger.handlers), logger.level, logger.propagate))
        return logger

    yield track

    for logger, handlers, level, propagate in saved:
        logger.handlers[:] = handlers
        logger.setLevel(level)
        logger.propagate = propagate


def _read_logger_attribute(restore_logger):
    return pydeflate_config.logger


def _call_setup_logger(restore_logger):
    logger = restore_logger("pydeflate.test_logging_setup")
    configured = pydeflate_config.setup_logger(logger.name)
    # Handler attachment is skipped when an ancestor (pytest's capture handler on
    # the root logger) already has one, so the level is the stable signal.
    assert configured is logger
    assert logger.level == logging.INFO
    return configured


@pytest.mark.parametrize(
    "call",
    [
        pytest.param(_read_logger_attribute, id="config-logger"),
        pytest.param(_call_setup_logger, id="setup-logger"),
    ],
)
def test_deprecated_name_warns(call, restore_logger):
    with pytest.warns(DeprecationWarning, match="3.0"):
        result = call(restore_logger)

    assert isinstance(result, logging.Logger)


def test_deprecated_logger_attribute_is_the_package_logger():
    with pytest.warns(DeprecationWarning):
        assert pydeflate_config.logger is logging.getLogger("pydeflate")


def test_unknown_config_attribute_raises():
    name = "no_such_name"
    with pytest.raises(AttributeError, match=name):
        getattr(pydeflate_config, name)
