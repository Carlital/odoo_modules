# -*- coding: utf-8 -*-

from odoo import SUPERUSER_ID, _, api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    pe_name = fields.Char("Guide Description", compute="_compute_pe_name", store=True)

    @api.depends("product_id", "sale_line_id")
    def _compute_pe_name(self):
        for move_id in self:
            # if move_id.purchase_line_id:
            #    move_id.pe_name = move_id.purchase_line_id.name or move_id.product_id.name
            if move_id.sale_line_id:
                move_id.pe_name = move_id.sale_line_id.name or move_id.product_id.name
            else:
                move_id.pe_name = move_id.product_id.name

    def action_pe_name_edit(self):
        self.ensure_one()
        view = self.env.ref(
            'l10n_pe_eguide.view_pe_stock_move_wizard_from'
        )
        context = dict(self.env.context)
        context['active_id'] = self.id
        context['active_ids'] = self.ids
        return {
            'name': _('Product Name'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pe.stock.move.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            # 'res_id': self.id,
            'context': context,
        }