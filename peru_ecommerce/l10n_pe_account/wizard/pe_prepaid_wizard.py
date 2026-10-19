from odoo import fields, models, api


class PeCPESend(models.TransientModel):
    _name = "pe.prepaid.wizard"
    _description = "Prepaid Payment Wizard"

    @api.model
    def _default_partner_id(self):
        move_line_id = self.env['account.move.line'].browse(self.env.context.get('active_ids', []))
        return move_line_id.move_id.partner_id or False

    @api.model
    def _default_move_id(self):
        move_line_id = self.env['account.move.line'].browse(self.env.context.get('active_ids', []))
        return move_line_id.pe_prepaid_invoice_id.id or False

    partner_id = fields.Many2one('res.partner', "Partner", default = _default_partner_id)
    move_id = fields.Many2one("account.move", "Invoice", default = _default_move_id,
                              domain="[('partner_id','=',partner_id),('state','=','posted'),('move_type','=','out_invoice')]")

    def apply_prepaid(self):
        self.ensure_one()
        move_line_id = self.env['account.move.line'].browse(self.env.context.get('active_ids', []))
        move_line_id.write({"pe_prepaid_invoice_id": self.move_id.id})
        return True

