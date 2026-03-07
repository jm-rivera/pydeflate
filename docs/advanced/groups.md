# Country Group Deflators

When deflating data denominated in a group currency like EUR, pydeflate needs a deflator for the group as a whole. By default it uses whatever aggregate the upstream data source (IMF, World Bank, OECD DAC) publishes. Starting in v2.4.0, you can instead compute GDP-weighted averages from member-country data, with full control over membership composition.

## The Problem

Source-published aggregates have limitations:

- **Opaque methodology** — IMF, World Bank, and OECD each compute the Euro Area aggregate differently. You can't inspect or reproduce the calculation.
- **Inconsistent membership** — Some sources lag behind membership changes. The IMF may not immediately reflect Croatia's 2023 accession in its Euro Area aggregate.
- **No counterfactual analysis** — Researchers often need "what if we used 2015 membership for all years?" to isolate composition effects from price effects.

## Treatment Modes

pydeflate offers three modes for computing group deflators:

### Source (default)

Use the data source's own published aggregate. This is backward-compatible — pydeflate behaves exactly as before.

```python
import pydeflate

# Default behavior, no configuration needed
result = pydeflate.imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="EUR",
    target_currency="USD",
)
```

### Fixed

GDP-weighted average of member countries' deflators, using **all-time membership** for every year. This makes the series comparable across time but is historically inaccurate for pre-accession years (e.g., Croatia's deflator is included in all years even though it joined in 2023).

```python
pydeflate.set_group_treatment("fixed")

result = pydeflate.imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="EUR",
    target_currency="USD",
)
```

### Dynamic

GDP-weighted average using the **actual membership in each year**. This is historically accurate (11 members in 1999, 20 in 2023) but creates composition-change artifacts at accession boundaries.

```python
pydeflate.set_group_treatment("dynamic")

result = pydeflate.imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="EUR",
    target_currency="EUR",
)
```

!!! tip "Choosing a mode"
    - Use **source** when you want to match published data exactly.
    - Use **fixed** when comparability across time matters more than historical accuracy.
    - Use **dynamic** when you need historically accurate membership composition.

## Per-Group Configuration

Configure a specific group independently from the global default:

```python
# Pin EMU membership to 2019 (pre-COVID, pre-Croatia)
pydeflate.configure_group("EMU", treatment="fixed", members_year=2019)

result = pydeflate.imf_gdp_deflate(
    data=df,
    base_year=2015,
    source_currency="EUR",
    target_currency="EUR",
)

# Reset when done
pydeflate.reset_group_config()
```

!!! note "EMU vs EUR"
    `"EMU"` identifies the **country group** (European Monetary Union). `"EUR"` is the **currency code** used in `source_currency` and `target_currency`. This distinction avoids ambiguity: `configure_group("EMU", ...)` configures the group, while `source_currency="EUR"` specifies the currency.

## Scoped Configuration

Use `pydeflate_session` to set group treatment for a block of code, with automatic cleanup:

```python
from pydeflate import pydeflate_session

with pydeflate_session(group_treatment="dynamic"):
    # Dynamic membership inside this block
    result = pydeflate.imf_gdp_deflate(
        data=df,
        base_year=2015,
        source_currency="EUR",
        target_currency="EUR",
    )

# Treatment automatically reverts to "source" here
```

This is useful in scripts that mix different treatment modes, or in applications where you want to avoid global state leaking between operations.

## Querying Membership

Inspect EMU membership at any point in time:

```python
>>> pydeflate.emu_members(1999)
['AUT', 'BEL', 'DEU', 'ESP', 'FIN', 'FRA', 'IRL', 'ITA', 'LUX', 'NLD', 'PRT']

>>> pydeflate.emu_members(2023)
['AUT', 'BEL', 'CYP', 'DEU', 'ESP', 'EST', 'FIN', 'FRA', 'GRC', 'HRV',
 'IRL', 'ITA', 'LTU', 'LUX', 'LVA', 'MLT', 'NLD', 'PRT', 'SVK', 'SVN']

>>> len(pydeflate.emu_members())  # all-time members
20
```

## How It Works

When a non-default treatment is active and you deflate with `source_currency="EUR"` (or `target_currency="EUR"`):

1. pydeflate resolves the currency code `"EUR"` to the registered group `"EMU"`.
2. It retrieves deflator values for each member country in the source data.
3. It computes a GDP-weighted average (using nominal GDP in USD as weights) for each year, replacing the group's aggregate deflator row.
4. If GDP data is unavailable for member countries, it falls back to equal-weight averaging.
5. The rest of the deflation pipeline proceeds as usual — exchange rates are **not** modified (they are market rates, not aggregates).

## Registering Custom Groups

The group system is extensible. You can register any country group:

```python
from pydeflate.groups import GroupDefinition, _registry

def asean_members(year: int) -> list[str]:
    """Return ASEAN member ISO3 codes."""
    members = ["BRN", "IDN", "KHM", "LAO", "MMR",
               "MYS", "PHL", "SGP", "THA", "VNM"]
    return sorted(members)

_registry.register(
    GroupDefinition(
        key="ASEAN",
        iso3="ASEAN",  # Must match the ISO3 code in your source data
        name="ASEAN",
        get_members=asean_members,
    )
)

# Now you can configure it
pydeflate.configure_group("ASEAN", treatment="fixed")
```

!!! warning
    Custom groups only work if the source data contains an aggregate row with a matching `pydeflate_iso3` code. The built-in IMF, World Bank, and OECD sources include Euro Area aggregates (`EUR`) but may not include other groupings.

## API Reference

| Function | Description |
|---|---|
| `set_group_treatment(treatment)` | Set the default treatment for all groups (`"source"`, `"fixed"`, or `"dynamic"`) |
| `configure_group(group, treatment=, members_year=)` | Configure a specific group by key (e.g., `"EMU"`) |
| `reset_group_config()` | Reset all group configurations to defaults |
| `emu_members(year=None)` | Return EMU member ISO3 codes (for a specific year, or all-time) |
| `pydeflate_session(group_treatment=)` | Context manager with scoped group treatment |

## Next Steps

- [**Deflation Guide**](../deflate.md) — All deflation methods with examples
- [**Context Management**](context.md) — Scoped configuration and parallel processing
- [**Plugin System**](plugins.md) — Register custom data sources
