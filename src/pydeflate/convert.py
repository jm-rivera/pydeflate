"""Public helper for resolving entity names to pydeflate codes.

Provides ``add_iso3``, an opt-in DataFrame helper that maps a column of
entity-name strings to pydeflate codes (ISO3 for countries; aggregate codes
for recognised groups) using the same resolvekit-backed resolution the
internal deflate pipeline uses.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from pydeflate.exceptions import ConfigurationError, UnmatchedEntitiesError
from pydeflate.pydeflate_config import logger
from pydeflate.sources.common import _match_name_to_iso3

_VALID_ON_UNMATCHED = frozenset({"warn", "raise", "ignore"})


def _apply_unmatched_policy(
    unmatched: list[str],
    on_unmatched: str,
) -> None:
    """Log or raise based on the on_unmatched policy.

    Args:
        unmatched: Sorted list of distinct values that failed resolution.
        on_unmatched: One of "warn", "raise", or "ignore".

    Raises:
        UnmatchedEntitiesError: If ``on_unmatched="raise"`` and unmatched is
            non-empty.
    """
    if not unmatched:
        return
    if on_unmatched == "raise":
        raise UnmatchedEntitiesError(unmatched)
    if on_unmatched == "warn":
        shown = unmatched[:20]
        suffix = f" (+{len(unmatched) - 20} more)" if len(unmatched) > 20 else ""
        logger.warning(
            "add_iso3 could not resolve %d value(s): %s%s",
            len(unmatched),
            shown,
            suffix,
        )
    # "ignore": do nothing


def add_iso3(
    data: pd.DataFrame,
    id_column: str,
    *,
    target_column: str = "iso_code",
    on_unmatched: Literal["warn", "raise", "ignore"] = "warn",
) -> pd.DataFrame:
    """Add a column of pydeflate codes resolved from an entity-name column.

    Resolves the values in ``id_column`` to pydeflate codes — ISO3 for
    countries; aggregate codes (EU, EMU, EUI, DAC, G7C, SSA, WLD, XXK) for
    recognised groups — using the same resolution pydeflate's deflate
    functions use internally. Returns a new DataFrame (the input is not
    mutated); the resolved codes are written to ``target_column``.

    Unresolved or ambiguous names never produce a wrong guess. Ambiguous
    names are also treated as unmatched (they arrive as ``None`` via
    ``on_ambiguous="null"``), so ``UnmatchedEntitiesError.unmatched`` can
    include ambiguous inputs. How unmatched values are reported is controlled
    by ``on_unmatched``.

    Args:
        data: Input DataFrame. Not mutated.
        id_column: Name of the column holding entity-name strings.
        target_column: Name of the column to write codes into
            (default ``"iso_code"``). Overwritten if it already exists.
        on_unmatched: Policy for values that don't resolve:
            ``"warn"`` (default) sets them to ``pd.NA`` and logs the distinct
            unmatched values at WARNING level; ``"raise"`` raises
            ``UnmatchedEntitiesError`` listing them; ``"ignore"`` sets them
            to ``pd.NA`` silently. Empty/null input cells are always
            ``pd.NA`` and are never treated as unmatched.

    Returns:
        A new DataFrame with ``target_column`` added.

    Raises:
        UnmatchedEntitiesError: If ``on_unmatched="raise"`` and any non-null
            value fails to resolve.
        ConfigurationError: If ``id_column`` is missing from ``data`` or
            ``on_unmatched`` is not one of ``"warn"``/``"raise"``/``"ignore"``.

    Examples:
        >>> import pandas as pd, pydeflate
        >>> df = pd.DataFrame({"country": ["France", "World", "Atlantis"]})
        >>> out = pydeflate.add_iso3(df, id_column="country")
        >>> out["iso_code"].tolist()
        ['FRA', 'WLD', <NA>]
    """
    if id_column not in data.columns:
        raise ConfigurationError(
            f"Column '{id_column}' not found in DataFrame.",
            parameter="id_column",
        )
    if on_unmatched not in _VALID_ON_UNMATCHED:
        raise ConfigurationError(
            f"Expected one of {sorted(_VALID_ON_UNMATCHED)!r}, got {on_unmatched!r}.",
            parameter="on_unmatched",
        )

    out = data.copy()
    col = out[id_column]

    non_null = col.dropna()
    unique_values = list(non_null.unique())

    mapping = _match_name_to_iso3(unique_values)

    unmatched = sorted({v for v, code in mapping.items() if code is None})
    _apply_unmatched_policy(unmatched, on_unmatched)

    out[target_column] = col.map(mapping)
    # Normalise: None entries from the mapping (unmatched) and null input cells
    # both land as pd.NA, including on pyarrow-backed frames where fillna(pd.NA)
    # can fail.
    out[target_column] = (
        out[target_column].astype("object").where(out[target_column].notna(), pd.NA)
    )

    return out
