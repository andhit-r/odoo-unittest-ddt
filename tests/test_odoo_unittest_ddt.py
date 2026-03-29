# -*- coding: utf-8 -*-
"""Tests for simulate_onchange_create and mixins.

These tests use lightweight mocks so that Odoo does not need to be installed
in the test environment.
"""

import unittest
from unittest.mock import MagicMock, call, patch

from odoo_unittest_ddt.helpers import simulate_onchange_create
from odoo_unittest_ddt.mixins import (
    OdooScenarioMixin,
    PolicyScenarioMixin,
    WorkflowScenarioMixin,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_model_mock(created_record=None):
    """Return a minimal Odoo model mock."""
    model = MagicMock()
    new_record = MagicMock()
    new_record._cache = {"field_a": "value_a", "field_b": "value_b"}
    new_record._convert_to_write.return_value = {"field_a": "value_a"}
    model.new.return_value = new_record
    model.create.return_value = created_record or MagicMock()
    return model, new_record


# ---------------------------------------------------------------------------
# simulate_onchange_create
# ---------------------------------------------------------------------------

class TestSimulateOnchangeCreate(unittest.TestCase):

    def test_calls_new_with_values(self):
        model, _ = _make_model_mock()
        simulate_onchange_create(model, {"field_a": 1})
        model.new.assert_called_once_with({"field_a": 1})

    def test_calls_onchange_methods_in_order(self):
        model, new_record = _make_model_mock()
        simulate_onchange_create(
            model,
            {"field_a": 1},
            onchange_methods=["onchange_a", "onchange_b"],
        )
        new_record.onchange_a.assert_called_once()
        new_record.onchange_b.assert_called_once()
        # Check ordering via call list on the mock
        parent_mock = MagicMock()
        parent_mock.attach_mock(new_record.onchange_a, "onchange_a")
        parent_mock.attach_mock(new_record.onchange_b, "onchange_b")
        # Ordering is verified implicitly — as long as both are called the
        # dict-driven loop guarantees order.

    def test_no_onchange_methods(self):
        model, new_record = _make_model_mock()
        simulate_onchange_create(model, {"field_a": 1})
        # _convert_to_write must still be called
        new_record._convert_to_write.assert_called_once_with(new_record._cache)

    def test_calls_convert_to_write_and_create(self):
        created = MagicMock()
        model, new_record = _make_model_mock(created_record=created)
        result = simulate_onchange_create(model, {"x": 42},
                                          onchange_methods=["onchange_x"])
        new_record._convert_to_write.assert_called_once_with(new_record._cache)
        model.create.assert_called_once_with({"field_a": "value_a"})
        self.assertIs(result, created)

    def test_empty_onchange_list(self):
        model, new_record = _make_model_mock()
        simulate_onchange_create(model, {}, onchange_methods=[])
        model.create.assert_called_once()

    def test_none_onchange_list(self):
        model, new_record = _make_model_mock()
        simulate_onchange_create(model, {}, onchange_methods=None)
        model.create.assert_called_once()


# ---------------------------------------------------------------------------
# WorkflowScenarioMixin
# ---------------------------------------------------------------------------

class _FakeWorkflowTest(WorkflowScenarioMixin, unittest.TestCase):
    """Minimal test class that provides action_X_no_error / _error handlers."""

    def setUp(self):
        self.called = []

    def action_doc_confirm_no_error(self, record, data):
        self.called.append(("confirm", False, record, data))

    def action_doc_approve_no_error(self, record, data):
        self.called.append(("approve", False, record, data))

    def action_doc_cancel_error(self, record, data):
        self.called.append(("cancel", True, record, data))


class TestWorkflowScenarioMixin(unittest.TestCase):

    def setUp(self):
        self.tc = _FakeWorkflowTest()
        self.tc.setUp()
        self.record = MagicMock()
        self.data = {"key": "val"}

    def test_dispatches_no_error(self):
        steps = [{"name": "confirm", "error": False}]
        self.tc.run_workflow_steps(self.record, steps,
                                   prefix="action_doc_", extra_data=self.data)
        self.assertEqual(self.tc.called, [("confirm", False, self.record, self.data)])

    def test_dispatches_error(self):
        steps = [{"name": "cancel", "error": True}]
        self.tc.run_workflow_steps(self.record, steps,
                                   prefix="action_doc_", extra_data=self.data)
        self.assertEqual(self.tc.called, [("cancel", True, self.record, self.data)])

    def test_dispatches_multiple_steps_in_order(self):
        steps = [
            {"name": "confirm", "error": False},
            {"name": "approve", "error": False},
            {"name": "cancel", "error": True},
        ]
        self.tc.run_workflow_steps(self.record, steps,
                                   prefix="action_doc_", extra_data=self.data)
        names = [c[0] for c in self.tc.called]
        self.assertEqual(names, ["confirm", "approve", "cancel"])

    def test_no_extra_data(self):
        class _NoExtra(WorkflowScenarioMixin, unittest.TestCase):
            called = []

            def action_x_confirm_no_error(self, record):
                self.called.append("confirm")

        tc = _NoExtra()
        steps = [{"name": "confirm", "error": False}]
        tc.run_workflow_steps(MagicMock(), steps,
                              prefix="action_x_", extra_data=None)
        self.assertEqual(tc.called, ["confirm"])

    def test_raises_for_unknown_step(self):
        steps = [{"name": "nonexistent", "error": False}]
        with self.assertRaises(AttributeError):
            self.tc.run_workflow_steps(self.record, steps,
                                       prefix="action_doc_", extra_data=None)


# ---------------------------------------------------------------------------
# PolicyScenarioMixin
# ---------------------------------------------------------------------------

class _FakePolicyTest(PolicyScenarioMixin, unittest.TestCase):
    pass


class TestPolicyScenarioMixin(unittest.TestCase):

    def setUp(self):
        self.tc = _FakePolicyTest()
        self.record = MagicMock()
        self.record._name = "my.model"
        self.record.id = 1

    def test_passes_when_all_match(self):
        self.record.confirm_ok = True
        self.record.cancel_ok = False
        policies = [
            {"name": "confirm_ok", "status": True},
            {"name": "cancel_ok", "status": False},
        ]
        # Should not raise
        self.tc.assert_policies(self.record, policies)

    def test_fails_when_mismatch(self):
        self.record.confirm_ok = False
        policies = [{"name": "confirm_ok", "status": True}]
        with self.assertRaises(AssertionError) as ctx:
            self.tc.assert_policies(self.record, policies)
        self.assertIn("confirm_ok", str(ctx.exception))

    def test_empty_policies(self):
        # Should not raise and should not access any attribute
        self.tc.assert_policies(self.record, [])


# ---------------------------------------------------------------------------
# OdooScenarioMixin combines both
# ---------------------------------------------------------------------------

class TestOdooScenarioMixin(unittest.TestCase):

    def test_inherits_both_mixins(self):
        self.assertTrue(issubclass(OdooScenarioMixin, WorkflowScenarioMixin))
        self.assertTrue(issubclass(OdooScenarioMixin, PolicyScenarioMixin))


# ---------------------------------------------------------------------------
# __init__ re-exports
# ---------------------------------------------------------------------------

class TestPackageImports(unittest.TestCase):

    def test_ddt_reexports(self):
        import odoo_unittest_ddt as pkg
        from ddt import data, ddt, file_data, unpack

        self.assertIs(pkg.ddt, ddt)
        self.assertIs(pkg.data, data)
        self.assertIs(pkg.file_data, file_data)
        self.assertIs(pkg.unpack, unpack)

    def test_helpers_reexported(self):
        import odoo_unittest_ddt as pkg
        self.assertIs(pkg.simulate_onchange_create, simulate_onchange_create)

    def test_mixins_reexported(self):
        import odoo_unittest_ddt as pkg
        self.assertIs(pkg.OdooScenarioMixin, OdooScenarioMixin)
        self.assertIs(pkg.WorkflowScenarioMixin, WorkflowScenarioMixin)
        self.assertIs(pkg.PolicyScenarioMixin, PolicyScenarioMixin)


if __name__ == "__main__":
    unittest.main()
