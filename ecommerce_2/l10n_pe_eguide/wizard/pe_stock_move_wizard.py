
from odoo import fields, models, api

class PeStockMoveWizard(models.TransientModel):
    _name = "pe.stock.move.wizard"

    @api.model
    def _default_move_name(self):
        id = self.env.context.get('active_id')
        move_id = self.env['stock.move'].browse(id)
        return move_id.pe_name

    @api.model
    def _default_move_id(self):
        return self.env.context.get('active_id') or False

    name = fields.Text("Description", default=_default_move_name)
    move_id = fields.Many2one("stock.move", "Stock Move", default=_default_move_id)

    def action_name_apply(self):
        self.ensure_one()
        return self.move_id.write({'pe_name': self.name})

