from odoo import fields, models, api

class Project(models.Model):
    _inherit = "project.project"

    @api.model
    def _create_analytic_account_from_values(self, values):
        return None

    def _create_analytic_account(self):
        for project in self:
            project.write({'analytic_account_id': None})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['analytic_account_id'] = None
        return super().create(vals_list)