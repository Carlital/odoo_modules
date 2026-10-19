from odoo import models, api

class ResCity(models.Model):
    _inherit = 'res.city'

    _sql_constraints = [
        ('city_name_state_unique', 'unique(name, state_id)', 'La ciudad ya existe para esa provincia.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('country_id') and vals.get('state_id'):
                state = self.env['res.country.state'].browse(vals['state_id'])
                if state:
                    vals['country_id'] = state.country_id.id
        return super().create(vals_list)

    def write(self, vals):
        # (state_id o country_id) sincroniza con provincia
        res = super().write(vals)
        if 'state_id' in vals or ('country_id' in vals and not vals.get('country_id')):
            for rec in self:
                if rec.state_id and rec.country_id != rec.state_id.country_id:
                    super(ResCity, rec).write({'country_id': rec.state_id.country_id.id})
        return res
