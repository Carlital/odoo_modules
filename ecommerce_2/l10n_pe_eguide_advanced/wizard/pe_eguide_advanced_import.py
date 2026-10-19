# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from librecpe import Servidor
from odoo.exceptions import ValidationError

class PeEguideAdvancedImport(models.TransientModel):
    _name = "pe.eguide.advanced.import"
    _description = "CPE Wizard"

    # partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    move_ids = fields.Many2many(comodel_name='account.move', string='Moves')
    picking_ids = fields.Many2many(comodel_name='stock.picking', string='Pickings')
    import_by = fields.Selection(selection=[('invoice', 'Invoice'), ('picking', 'Picking')], string='Import by', default='invoice')

    def get_guide_lines(self):
        lines = []
        if self.move_ids and self.import_by == 'invoice':
            line_ids = self.move_ids.mapped('invoice_line_ids').filtered(
                lambda x: x.product_id and x.product_id.detailed_type != 'service')
            if not line_ids:
                raise ValidationError(_("There are no products in the selected invoices"))
            product_ids = line_ids.mapped('product_id')
            for product_id in product_ids:
                if not product_id.default_code:
                    raise ValidationError(_("Product %s has no code") % product_id.name)
                quantity = 0.0
                invoice_line_ids = line_ids.filtered(lambda x: x.product_id == product_id)
                for line_id in invoice_line_ids:
                    quantity += line_id.product_uom_id._compute_quantity(line_id.quantity, line_id.product_id.uom_id)

                lines.append((0, 0, {
                    'product_code': product_id.default_code,
                    'quantity': quantity,
                    'uom_code': product_id.uom_id.pe_unit_code or 'NIU',
                    'name': product_id.name,
                    'product_id': product_id.id,
                    'invoice_line_ids': [(6, 0, invoice_line_ids.ids)]
                }))
        elif self.picking_ids and self.import_by == 'picking':
            line_ids = self.picking_ids.mapped('move_ids_without_package')
            if not line_ids:
                raise ValidationError(_("There are no products in the selected pickings"))
            product_ids = line_ids.mapped('product_id')
            for product_id in product_ids:
                if not product_id.default_code:
                    raise ValidationError(_("Product %s has no code") % product_id.name)
                quantity = 0.0
                stock_move_ids = line_ids.filtered(lambda x: x.product_id == product_id)
                for line_id in stock_move_ids:
                    quantity += line_id.product_uom._compute_quantity(line_id.product_uom_qty,
                                                                      line_id.product_id.uom_id)
                lines.append((0, 0, {
                    'product_code': product_id.default_code,
                    'quantity': quantity,
                    'uom_code': product_id.uom_id.pe_unit_code or 'NIU',
                    'name': product_id.name,
                    'product_id': product_id.id,
                    'stock_move_ids': [(6, 0, stock_move_ids.ids)]
                }))
        return lines

    def get_invoice_related(self):
        self.ensure_one()
        lines = []
        if self.move_ids:
            for move_id in self.move_ids:
                lines.append((0, 0, {
                            'name': move_id.l10n_latam_document_number,
                            'partner_id': move_id.partner_id.id,
                            'document_type': move_id.pe_invoice_code,
                            }))
        return lines

    def action_import(self):
        self.ensure_one()
        guide_id = self.env['pe.electronic.guide'].browse(self._context.get('active_id'))
        if not guide_id:
            return {}
        # guide_id.line_ids.unlink()
        line_ids = self.get_guide_lines()
        if not line_ids:
            raise ValidationError(_("There are no products to import"))
        # new_lines = []
        # for line_vals in line_ids:
        #     if line_vals[2].get('product_id'):
        #         line_id = guide_id.line_ids.filtered(lambda x: x.product_id.id == line_vals[2].get('product_id'))
        #         if line_id:
        #             line_id.quantity += line_id[2].get('quantity')
        #         else:
        #             new_lines.append((0, 0, line_vals[2]))
        guide_id.write({'line_ids': line_ids})
        return {}
