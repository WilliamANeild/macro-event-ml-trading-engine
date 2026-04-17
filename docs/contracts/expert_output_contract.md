# Expert Output Contract

Canonical reference for the `ExpertPrediction` dataclass emitted by every
expert module. Downstream consumers (MetaStacker, ExpressionSelector) depend
on this schema -- any changes here require a version bump in `model_version`.

Source of truth: `src/engine/experts/schemas.py`

---

## ExpertPrediction Schema

| Field                | Type                          | Required | Description |
|----------------------|-------------------------------|----------|-------------|
| `expert_name`        | `str`                         | yes      | Unique identifier for the expert that produced this prediction. |
| `as_of_date`         | `date`                        | yes      | The date the prediction applies to. |
| `theme`              | `str`                         | yes      | Top-level theme from the keyword taxonomy (e.g. `CONFLICT_ESCALATION`). |
| `subtheme`           | `str`                         | yes      | Sub-theme within the sleeve (e.g. `RedSea`). |
| `probability_active` | `float`                       | yes      | Probability that the event type is currently active. |
| `severity_score`     | `float`                       | yes      | How severe the detected event is (higher = more severe). |
| `confidence_score`   | `float`                       | yes      | Model confidence in its own prediction. |
| `direction`          | `str`                         | yes      | Recommended position direction. |
| `tags`               | `list[str]`                   | no       | Free-form tags for filtering and grouping. Defaults to `[]`. |
| `metadata`           | `dict[str, Any]`              | no       | Auxiliary information. Defaults to `{}`. See Metadata section below. |
| `localization`       | `LocalizationMetadata | None` | no       | Geographic or asset-class scope of the signal. Defaults to `None`. |
| `model_version`      | `str`                         | no       | Semantic version of the expert model. Defaults to `"v0.1"`. |

---

## Validation Rules

These constraints are enforced in `ExpertPrediction.__post_init__` and will
raise `ValueError` on construction if violated.

### Unit-interval floats

All three probability/score fields must satisfy `0.0 <= value <= 1.0`:

- `probability_active`
- `severity_score`
- `confidence_score`

Values outside this range are rejected, not silently clamped. Producers must
ensure values are within bounds before constructing the dataclass.

### Direction enum

`direction` must be one of:

- `"long"` -- the expert expects the relevant asset(s) to appreciate.
- `"short"` -- the expert expects the relevant asset(s) to decline.
- `"neutral"` -- no directional conviction; the signal is informational only.

Any other string raises `ValueError`.

---

## Localization

The optional `localization` field uses the `LocalizationMetadata` dataclass:

| Field            | Type               | Description |
|------------------|--------------------|-------------|
| `location_type`  | `LocalizationType` | One of `REGION`, `CHOKEPOINT`, `PORT_CLUSTER`, `COMMODITY`, `COUNTRY`. |
| `location_value` | `str`              | Freeform identifier (e.g. `"Suez"`, `"crude_oil"`, `"US"`). |
| `region`         | `str | None`       | Optional broader region grouping. |
| `subregion`      | `str | None`       | Optional subregion detail. |

A `LocalizationMetadata` can be built from a dict via
`LocalizationMetadata.from_dict(data)`.

---

## Metadata Convention

The `metadata` dict is unstructured, but producers should include:

| Key                    | Type             | Description |
|------------------------|------------------|-------------|
| `expert_family`        | `str`            | The `ExpertFamily` enum value (e.g. `"conflict_escalation"`, `"shipping_chokepoint"`). |
| `method`               | `str`            | `"model"` if the prediction comes from a trained ML model, `"heuristic"` if rule-based. |
| `feature_importances`  | `dict[str, float]` | Map of feature name to importance weight. Useful for explainability and debugging. |

---

## Downstream Consumer Guide

### MetaStacker

The MetaStacker aggregates predictions from multiple experts into a single
portfolio signal. It reads:

- `probability_active` -- used as the primary activation gate. Predictions
  with low probability are down-weighted or filtered out.
- `severity_score` -- used as a multiplier on position sizing. Higher severity
  leads to larger allocations when the signal is active.
- `confidence_score` -- used to weight this expert relative to others in the
  ensemble. Experts with higher confidence receive more influence.
- `direction` -- determines the sign of the position. `"neutral"` predictions
  are excluded from directional aggregation.
- `localization` -- used for geographic/asset deconfliction so that experts
  covering different regions do not cancel each other out.

### ExpressionSelector

The ExpressionSelector chooses which instruments to express a given trade
through. It reads:

- `direction` -- determines whether to look for long or short instruments.
- `localization` -- narrows the instrument universe to the relevant region,
  chokepoint, or commodity.
- `severity_score` -- higher severity may trigger the use of options or
  leveraged expressions via the derivatives overlay.
- `metadata.expert_family` -- used to route to family-specific expression
  logic (e.g. shipping chokepoint experts map to tanker and freight ETFs).
