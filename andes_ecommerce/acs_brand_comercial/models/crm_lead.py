
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _get_brand_default(self):
        return self.env.user.brand_id.id
    brand_comercial_id = fields.Many2one(
        'brand.comercial.tours',
        'Marca comercial', default=_get_brand_default)
    custom_template_mail_invoice_id = fields.Many2one(
        'mail.template',
        string='Plantilla correo facturación',
        related='brand_comercial_id.custom_template_mail_invoice_id')
    is_salesman = fields.Boolean('Es un vendedor')

    @api.model
    def _onchange_user_values(self, user_id):
        res = super()._onchange_user_values(user_id)
        res.update({
            'brand_comercial_id': False,
            'is_salesman': False})
        if user_id in self.env.ref(
                'acs_brand_comercial.group_brand_salesman').users.ids:
            user = self.env['res.users'].browse(user_id)
            res.update({
                'brand_comercial_id': user.brand_id,
                'is_salesman': True,
            })
        return res

    # @api.model
    # def search(self, args, offset=0, limit=None, order=None, count=False):
    #     res = super(CrmLead,self).search(args, offset, limit, order, count)
    #     user = self.env.user
    #     if user in self.env.ref(
    #         'acs_brand_comercial.group_brand_salesman').users:
    #         if not isinstance(res, int):
    #             res = self.browse([rec.id for rec in res if rec.user_id == user])
    #     return res
