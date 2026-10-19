# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_eguide_advanced_from_picking(self):
        partner_ids = self.mapped('partner_id')
        picking_type_ids = self.mapped('picking_type_id')
        guide_ids = self.env['pe.electronic.guide']
        if partner_ids:
            for partner_id in partner_ids:
                for picking_type_id in picking_type_ids:
                    picking_ids = self.filtered(lambda s: s.partner_id == partner_id and s.picking_type_id == picking_type_id)
                    if picking_type_id.code == 'incoming':
                        reason_transfer = '02'
                    elif picking_type_id.code == 'outgoing':
                        reason_transfer = '01'
                    else:
                        reason_transfer = '04'
                    if picking_ids:
                        line_ids = picking_ids.mapped('move_ids_without_package')
                        gross_weight = 0.0
                        unit_quantity = 0.0
                        for line_id in line_ids:
                            gross_weight += line_id.product_id.weight * line_id.product_uom_qty
                            unit_quantity += line_id.product_uom_qty
                        guide_id = self.env['pe.electronic.guide'].create({
                            'reason_transfer': reason_transfer,
                            'partner_id': partner_id.parent_id.id or partner_id.id,
                            'date_issue': fields.Datetime.now(),
                            'transfer_date': fields.Date.context_today(self),
                            'gross_weight': gross_weight or 1.0,
                            'gross_weight_unit': 'KGM',
                            'unit_quantity': unit_quantity or 1.0,
                            'transport_mode': '01',
                        })
                        guide_ids |= guide_id
                        guide_id._onchange_session_id()
                        guide_id._change_partner_id(partner_id)
                        self.with_context(**{'active_id': guide_id.id}).env['pe.eguide.advanced.import'].create({
                            'picking_ids': [(6, 0, picking_ids.ids)],
                            'import_by': 'picking'
                        }).action_import()

        action = self.env['ir.actions.actions']._for_xml_id('l10n_pe_eguide_advanced.action_pe_electronic_guide')
        if len(guide_ids) > 1:
            action['domain'] = [('id', 'in', guide_ids.ids)]
        elif len(guide_ids) == 1:
            form_view = [(self.env.ref('l10n_pe_eguide_advanced.view_pe_electronic_guide_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = guide_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action