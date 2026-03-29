# odoo-unittest-ddt

[![PyPI](https://img.shields.io/pypi/v/odoo-unittest-ddt)](https://pypi.org/project/odoo-unittest-ddt/)
[![Python](https://img.shields.io/pypi/pyversions/odoo-unittest-ddt)](https://pypi.org/project/odoo-unittest-ddt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

DDT (Data-Driven Tests) helpers and mixins for Odoo unit testing.

Reduces boilerplate when writing YAML-driven scenario tests for Odoo modules
by providing three core abstractions on top of the
[`ddt`](https://pypi.org/project/ddt/) library:

| Abstraction | Replaces |
|---|---|
| `simulate_onchange_create()` | `new()` → onchange loop → `_convert_to_write` → `create()` |
| `WorkflowScenarioMixin.run_workflow_steps()` | Manual `for step in workflow_steps` dispatch loop |
| `PolicyScenarioMixin.assert_policies()` | Manual `for policy in policies` assertion loop |

---

## Installation

```bash
pip install odoo-unittest-ddt
```

---

## Usage

### Before (without the library)

```python
# tests/test_workflow_asset.py
from ddt import ddt, file_data
from .base import BaseCase

@ddt
class TestWorkflowAsset(BaseCase):

    @file_data("scenario_asset_workflow.yaml")
    def test_workflow_asset(self, attribute, workflow_steps):
        category = getattr(self, attribute["category_name"])

        # --- boilerplate: simulate onchange before create ---
        dt_start = datetime(date.today().year, 1, 1) + relativedelta(...)
        values = {
            "category_id": category.id,
            "type": "normal",
            "name": "Test Asset",
            "purchase_value": attribute["purchase_value"],
            ...
        }
        rec_cache = self.obj_asset.new(values)
        rec_cache.onchange_category_id()
        rec_cache.onchange_date_min_prorate()
        rec_cache.onchange_amount_depreciation_line()
        # ... more onchange calls ...
        values = rec_cache._convert_to_write(rec_cache._cache)
        asset = self.obj_asset.create(values)
        # --- end boilerplate ---

        # --- boilerplate: dispatch workflow steps ---
        for workflow_step in workflow_steps:
            method_name = "action_asset_" + workflow_step["name"]
            if workflow_step["error"]:
                method_name += "_error"
            else:
                method_name += "_no_error"
            method_to_run = getattr(self, method_name)
            method_to_run(asset, attribute)
        # --- end boilerplate ---
```

### After (with the library)

```python
# tests/test_workflow_asset.py
from ddt import ddt, file_data
from odoo_unittest_ddt import OdooScenarioMixin, simulate_onchange_create
from odoo.tests.common import TransactionCase

@ddt
class TestWorkflowAsset(OdooScenarioMixin, TransactionCase):

    @file_data("scenario_asset_workflow.yaml")
    def test_workflow_asset(self, attribute, workflow_steps):
        asset = simulate_onchange_create(
            self.obj_asset,
            {
                "category_id": getattr(self, attribute["category_name"]).id,
                "type": "normal",
                "name": "Test Asset",
                "purchase_value": attribute["purchase_value"],
                "salvage_value": attribute["salvage_value"],
            },
            onchange_methods=[
                "onchange_category_id",
                "onchange_date_min_prorate",
                "onchange_amount_depreciation_line",
                "onchange_line_date_depreciation_line",
                "onchange_method_time",
            ],
        )
        self.run_workflow_steps(asset, workflow_steps,
                                prefix="action_asset_", extra_data=attribute)
```

---

## Reference

### `simulate_onchange_create(model_obj, values, onchange_methods=None)`

Creates an Odoo record using the standard `new()` → onchange chain → `create()` flow.

| Parameter | Type | Description |
|---|---|---|
| `model_obj` | `Model` | Odoo model recordset, e.g. `self.env["account.asset.asset"]` |
| `values` | `dict` | Initial field values passed to `model.new()` |
| `onchange_methods` | `list[str]` | Ordered list of onchange method names to call |

Returns the newly created persistent record.

---

### `WorkflowScenarioMixin.run_workflow_steps(record, steps, prefix="action_", extra_data=None)`

Iterates *steps* (a list of `{name, error}` dicts) and calls the matching
method on the test class.

For each step the resolved method name is:

```
<prefix> + <step["name"]> + "_error"      # when step["error"] is True
<prefix> + <step["name"]> + "_no_error"   # otherwise
```

YAML step format:

```yaml
workflow_steps:
  - name: confirm
    error: false
  - name: approve
    error: false
  - name: cancel
    error: true
```

---

### `PolicyScenarioMixin.assert_policies(record, policies)`

Iterates *policies* (a list of `{name, status}` dicts) and calls
`self.assertEqual(getattr(record, name), status)` for each one.

YAML policy format:

```yaml
policies:
  - name: confirm_ok
    status: true
  - name: cancel_ok
    status: false
```

---

### `OdooScenarioMixin`

Combined mixin inheriting both `WorkflowScenarioMixin` and `PolicyScenarioMixin`.

---

### Re-exported from `ddt`

For convenience, `ddt`, `data`, `file_data`, and `unpack` are re-exported
from `odoo_unittest_ddt` so you only need one import in your test files:

```python
from odoo_unittest_ddt import ddt, file_data, OdooScenarioMixin, simulate_onchange_create
```

---

## Full example with workflow and policy tests

**`scenario_my_workflow.yaml`**:

```yaml
scenario1:
  attribute:
    category_name: "asset_category_building"
    purchase_value: 500000000.0
    salvage_value: 0.0
  workflow_steps:
    - name: confirm
      error: false
    - name: approve
      error: false
```

**`scenario_my_policy.yaml`**:

```yaml
scenario1:
  attribute:
    user: user1
    groups:
      - group_employee
  policies:
    - name: confirm_ok
      status: true
    - name: cancel_ok
      status: false
```

**`tests/test_my_module.py`**:

```python
from odoo_unittest_ddt import (
    OdooScenarioMixin,
    ddt,
    file_data,
    simulate_onchange_create,
)
from odoo.tests.common import TransactionCase


@ddt
class TestMyWorkflow(OdooScenarioMixin, TransactionCase):

    @file_data("scenario_my_workflow.yaml")
    def test_workflow(self, attribute, workflow_steps):
        record = simulate_onchange_create(
            self.env["my.model"],
            {"name": "Test", "value": attribute["purchase_value"]},
            onchange_methods=["onchange_name"],
        )
        self.run_workflow_steps(record, workflow_steps,
                                prefix="action_my_", extra_data=attribute)

    def action_my_confirm_no_error(self, record, data):
        record.action_confirm()
        self.assertEqual(record.state, "confirm")

    def action_my_approve_no_error(self, record, data):
        record.action_approve()
        self.assertEqual(record.state, "approved")


@ddt
class TestMyPolicy(OdooScenarioMixin, TransactionCase):

    @file_data("scenario_my_policy.yaml")
    def test_policy(self, attribute, policies):
        self.env.user.groups_id = ...  # set up groups from attribute
        record = self.env["my.model"].search([], limit=1)
        self.assert_policies(record, policies)
```

---

## Compatibility

| Odoo version | Python | Status |
|---|---|---|
| 8.0 / 9.0 | 2.7 / 3.x | Uses `openerp` namespace — works if `_convert_to_write` is available |
| 10.0 – 17.0 | 3.x | Fully supported |

---

## Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/my-feature`.
3. Install dev dependencies: `pip install -e ".[dev]"`.
4. Run tests: `pytest`.
5. Open a pull request.

---

## License

MIT — see [LICENSE](LICENSE).
