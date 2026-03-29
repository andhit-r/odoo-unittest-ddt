# -*- coding: utf-8 -*-
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License MIT (https://opensource.org/licenses/MIT).

"""
odoo-unittest-ddt
~~~~~~~~~~~~~~~~~

DDT (Data-Driven Tests) helpers and mixins for Odoo unit testing.

Provides:
- Re-exports of ``ddt``, ``data``, ``file_data``, ``unpack`` for convenience.
- :func:`simulate_onchange_create` — shorthand for the Odoo
  ``new()`` → onchange chain → ``create()`` pattern.
- :class:`WorkflowScenarioMixin` — ``run_workflow_steps()`` helper that
  dispatches to ``action_<name>_no_error / action_<name>_error`` methods.
- :class:`PolicyScenarioMixin` — ``assert_policies()`` helper that checks
  boolean/value policy fields on a record.
- :class:`OdooScenarioMixin` — combined mixin for convenience.

Typical usage in an Odoo test module::

    from ddt import ddt, file_data
    from odoo_unittest_ddt import OdooScenarioMixin, simulate_onchange_create
    from odoo.tests.common import TransactionCase

    @ddt
    class TestMyWorkflow(OdooScenarioMixin, TransactionCase):

        @file_data("scenario_my_workflow.yaml")
        def test_my_workflow(self, attribute, workflow_steps):
            record = simulate_onchange_create(
                self.env["my.model"],
                {"field_a": attribute["field_a"]},
                onchange_methods=["onchange_field_a"],
            )
            self.run_workflow_steps(record, workflow_steps,
                                    prefix="action_my_", extra_data=attribute)
"""

from ddt import data, ddt, file_data, unpack

from .helpers import resolve_record_ids, simulate_onchange_create
from .mixins import OdooScenarioMixin, PolicyScenarioMixin, WorkflowScenarioMixin

__version__ = "0.1.0"

__all__ = [
    # ddt re-exports
    "ddt",
    "data",
    "file_data",
    "unpack",
    # helpers
    "simulate_onchange_create",
    "resolve_record_ids",
    # mixins
    "OdooScenarioMixin",
    "WorkflowScenarioMixin",
    "PolicyScenarioMixin",
]
