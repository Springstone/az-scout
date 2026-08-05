"""Core version compatibility check for plugin dependencies."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


def get_core_version() -> str:
    """Return the running az-scout version string."""
    from az_scout import __version__

    return __version__


def _version_satisfies(version: str, specifier: str) -> bool | None:
    """Return whether *version* satisfies the PEP 440 *specifier*.

    Returns ``None`` when the check cannot be performed — either :mod:`packaging`
    is unavailable or one of the inputs is unparseable.  Callers treat ``None``
    as "cannot verify", never as an incompatibility.
    """
    try:
        from packaging.specifiers import InvalidSpecifier, SpecifierSet
        from packaging.version import InvalidVersion, Version
    except ImportError as exc:  # pragma: no cover - packaging is a declared dependency
        logger.warning(
            "packaging is not installed — skipping az-scout version compatibility check: %s",
            exc,
        )
        return None

    try:
        return Version(version) in SpecifierSet(specifier)
    except (InvalidSpecifier, InvalidVersion) as exc:
        logger.warning(
            "Could not parse az-scout version specifier '%s': %s",
            specifier,
            exc,
        )
        return None


def check_core_version_compat(
    dependencies: list[str],
) -> tuple[bool, str]:
    """Check if a plugin's dependencies are compatible with the running core version.

    Parses the ``az-scout`` version specifier from *dependencies* and checks it
    against the running version.

    Returns ``(ok, message)`` — *ok* is ``True`` if compatible or if no version
    constraint is specified.  *message* is empty on success or describes the
    incompatibility.
    """
    core_version = get_core_version()

    # Dev versions (e.g. "0.0.0-dev", "2026.3.9.dev4") skip the check
    if "dev" in core_version or core_version == "0.0.0":
        return True, ""

    # Find the az-scout dependency with its version specifier
    for dep in dependencies:
        dep_lower = dep.strip().lower()
        # Extract the package name (before any version specifier)
        name_match = re.match(r"^([a-z0-9_-]+)", dep_lower.replace("_", "-"))
        if not name_match:
            continue
        name = name_match.group(1)
        if name != "az-scout":
            continue

        # Extract the version specifier part (everything after the name)
        specifier_str = dep.strip()[len(name_match.group(0)) :].strip()
        if not specifier_str:
            return True, ""  # No version constraint — always compatible

        # ``None`` means the check could not be performed — don't block the install
        if _version_satisfies(core_version, specifier_str) is False:
            return False, (
                f"Plugin requires az-scout{specifier_str} but this instance "
                f"runs v{core_version}. Upgrade az-scout first."
            )

        return True, ""

    # az-scout not in dependencies — no constraint to check
    return True, ""
