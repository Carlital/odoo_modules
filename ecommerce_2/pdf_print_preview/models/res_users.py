# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    preview_print = fields.Boolean(
        string="Preview print",
        default=True
    )

    automatic_printing = fields.Boolean(
        string="Automatic printing"
    )

    def preview_reload(self):
        return {
            "type": "ir.actions.client",
            "tag": "reload"
        }

    def preview_print_save(self):
        return {
            "type": "ir.actions.client",
            "tag": "reload_context"
        }

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["preview_print", "automatic_printing"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["preview_print", "automatic_printing"]
