# -*- coding: utf-8 -*-
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License MIT (https://opensource.org/licenses/MIT).

"""
Mixins that add DDT scenario-testing helpers to an Odoo ``TransactionCase``.
"""


class WorkflowScenarioMixin:
    """Mixin for YAML-driven workflow scenario tests.

    Provides :meth:`run_workflow_steps` which iterates over a list of step
    dicts (as loaded from YAML via ``@file_data``) and dispatches each step to
    the corresponding ``action_<prefix><name>_no_error`` or
    ``action_<prefix><name>_error`` method defined on the test class.

    **YAML step format**::

        workflow_steps:
          - name: confirm
            error: false
          - name: approve
            error: false
          - name: cancel
            error: true

    **Test class example**::

        from ddt import ddt, file_data
        from odoo_unittest_ddt import WorkflowScenarioMixin
        from odoo.tests.common import TransactionCase

        @ddt
        class TestMyWorkflow(WorkflowScenarioMixin, TransactionCase):

            @file_data("scenario_my_workflow.yaml")
            def test_my_workflow(self, attribute, workflow_steps):
                record = self._create_record(attribute)
                self.run_workflow_steps(record, workflow_steps,
                                        prefix="action_my_", extra_data=attribute)

            def action_my_confirm_no_error(self, record, data):
                record.action_confirm()
                self.assertEqual(record.state, "confirm")

            def action_my_cancel_error(self, record, data):
                with self.assertRaises(Exception):
                    record.action_cancel()
    """

    def run_workflow_steps(self, record, steps, prefix="action_", extra_data=None):
        """Execute a sequence of workflow steps on *record*.

        For each step dict, the method
        ``self.<prefix><name>_no_error(record, extra_data)`` or
        ``self.<prefix><name>_error(record, extra_data)`` is called,
        depending on the value of ``step["error"]``.

        :param record:
            The Odoo record under test.
        :param list[dict] steps:
            List of dicts, each with at minimum the keys:

            ``name`` (*str*)
                Logical name of the step, appended to *prefix*.
            ``error`` (*bool*)
                When ``True``, the ``…_error`` variant is called; otherwise
                the ``…_no_error`` variant is called.

        :param str prefix:
            Method-name prefix to use when resolving the handler.
            Defaults to ``"action_"``.
        :param extra_data:
            Optional extra argument passed as the second positional argument
            to every handler.  Typically the ``attribute`` dict from the
            YAML scenario.  When ``None`` handlers are called with only the
            *record*.
        """
        for step in steps:
            suffix = "_error" if step.get("error", False) else "_no_error"
            method_name = prefix + step["name"] + suffix
            method = getattr(self, method_name)
            if extra_data is not None:
                method(record, extra_data)
            else:
                method(record)


class PolicyScenarioMixin:
    """Mixin for YAML-driven policy scenario tests.

    Provides :meth:`assert_policies` which iterates over a list of policy
    dicts (as loaded from YAML via ``@file_data``) and asserts the value of
    the corresponding field on the record.

    **YAML policy format**::

        policies:
          - name: confirm_ok
            status: true
          - name: cancel_ok
            status: false

    **Test class example**::

        from ddt import ddt, file_data
        from odoo_unittest_ddt import PolicyScenarioMixin
        from odoo.tests.common import TransactionCase

        @ddt
        class TestMyPolicy(PolicyScenarioMixin, TransactionCase):

            @file_data("scenario_my_policy.yaml")
            def test_my_policy(self, attribute, policies):
                record = self._create_record(attribute)
                self.assert_policies(record, policies)
    """

    def assert_policies(self, record, policies):
        """Assert that policy fields on *record* match the expected values.

        :param record:
            The Odoo record under test.
        :param list[dict] policies:
            List of dicts, each with the keys:

            ``name`` (*str*)
                Field name on the record.
            ``status`` (*bool* or any scalar)
                Expected field value.

        Each failed assertion produces a descriptive message that includes the
        policy name and the model name.
        """
        for policy in policies:
            field_name = policy["name"]
            expected = policy["status"]
            actual = getattr(record, field_name)
            self.assertEqual(
                actual,
                expected,
                msg=(
                    "Policy '{field}' on <{model} id={rec_id}>: "
                    "expected {expected!r}, got {actual!r}".format(
                        field=field_name,
                        model=record._name,
                        rec_id=record.id,
                        expected=expected,
                        actual=actual,
                    )
                ),
            )


class OdooScenarioMixin(WorkflowScenarioMixin, PolicyScenarioMixin):
    """Combined mixin exposing both :class:`WorkflowScenarioMixin` and
    :class:`PolicyScenarioMixin`.

    Import this single class when the test module requires both workflow and
    policy helpers::

        from odoo_unittest_ddt import OdooScenarioMixin

        @ddt
        class TestMyModule(OdooScenarioMixin, TransactionCase):
            ...
    """
