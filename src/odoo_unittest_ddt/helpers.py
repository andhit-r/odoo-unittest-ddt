# -*- coding: utf-8 -*-
# Copyright 2024 PT. Simetri Sinergi Indonesia
# License MIT (https://opensource.org/licenses/MIT).

"""
Low-level helper functions for Odoo DDT unit testing.
"""


def simulate_onchange_create(model_obj, values, onchange_methods=None):
    """Create an Odoo record by simulating ``new()`` → onchange → ``create()``.

    This is the standard Odoo pattern for creating records whose fields depend
    on onchange methods being executed prior to persistence.  Without calling
    the onchange methods the related/computed fields would be empty or wrong.

    :param model_obj:
        An Odoo model recordset, usually obtained via ``self.env["model.name"]``
        or ``self.obj_<something>`` in the test's ``setUp``.
    :param dict values:
        Initial field values to pass to ``model.new()``.
    :param list[str] onchange_methods:
        Ordered list of onchange method names to call on the transient record
        before converting it to a persistent one.  Pass ``None`` or ``[]``
        when no onchange methods are required.
    :returns: Newly created persistent Odoo record.

    **Example**::

        asset = simulate_onchange_create(
            self.obj_asset,
            {
                "category_id": category.id,
                "type": "normal",
                "name": "Test Asset",
                "purchase_value": 500_000_000.0,
            },
            onchange_methods=[
                "onchange_category_id",
                "onchange_date_min_prorate",
                "onchange_amount_depreciation_line",
            ],
        )
    """
    record = model_obj.new(values)
    for method_name in onchange_methods or []:
        getattr(record, method_name)()
    write_values = record._convert_to_write(record._cache)
    return model_obj.create(write_values)


def resolve_record_ids(test_instance, attribute, exclude_keys=None):
    """Resolve ``*_name`` keys in *attribute* to Odoo record ``.id`` values.

    A common YAML-driven test pattern stores fixture attribute names as
    ``<field>_name`` (e.g. ``school_name: "school"``) instead of raw IDs so
    that the scenario files stay human-readable.  This helper converts those
    entries into the ``<field>_id`` integers that Odoo ``create()`` expects,
    by looking up ``getattr(test_instance, value).id`` for every key that ends
    with ``"_name"``.

    Keys in *exclude_keys* are dropped from the result entirely — useful for
    meta-keys such as ``"user"`` or ``"description"`` that exist only for
    scenario bookkeeping and must not reach ``create()``.

    ``_name`` entries whose value is falsy (``None``, ``""``, etc.) are silently
    skipped so that optional relation fields can be omitted from a scenario
    without raising an ``AttributeError``.

    All other keys are passed through unchanged (e.g. plain scalar fields such
    as ``date``).

    :param test_instance:
        The test instance — ``self`` inside a test method.
    :param dict attribute:
        Attribute dict, typically the ``attribute`` value from a
        ``@file_data`` YAML scenario.
    :param list[str] exclude_keys:
        Keys to omit from the result entirely.  Defaults to ``None`` (nothing
        excluded).
    :returns:
        A new ``dict`` ready to be passed to ``env["model.name"].create()``.

    **Example**::

        def _create_enrollment(self, attribute):
            vals = resolve_record_ids(
                self, attribute, exclude_keys=["user", "description"]
            )
            vals["currency_id"] = self.env.company.currency_id.id
            return self.env["school_enrollment"].create(vals)
    """
    exclude_keys = set(exclude_keys or [])
    result = {}
    for key, value in attribute.items():
        if key in exclude_keys:
            continue
        if key.endswith("_name"):
            if value:  # skip falsy — optional relation not set in this scenario
                id_key = key[:-5] + "_id"
                result[id_key] = getattr(test_instance, value).id
        else:
            result[key] = value
    return result
