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
