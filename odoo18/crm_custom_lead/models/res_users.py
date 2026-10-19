from odoo import models, api


CUSTOM_GROUP_XMLIDS = [
    'crm_custom_lead.group_asesor',
    'crm_custom_lead.group_validador',
    'crm_custom_lead.group_post_venta',
    'crm_custom_lead.group_back_office',
    'crm_custom_lead.group_gerente',
    'crm_custom_lead.group_jefe_operaciones',
    'crm_custom_lead.group_supervisor',
]

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _ensure_internal_when_custom_group(self):
        if self.env.context.get('skip_group_enforce'):
            return
        group_user = self.env.ref('base.group_user')
        group_portal = self.env.ref('base.group_portal')
        group_public = self.env.ref('base.group_public')
        custom_groups = [self.env.ref(x) for x in CUSTOM_GROUP_XMLIDS]
        for user in self:
            if any(user.has_group(x) for x in CUSTOM_GROUP_XMLIDS):
                # add internal, remove portal/public user
                user.with_context(skip_group_enforce=True).write({
                    'groups_id': [
                        (4, group_user.id),
                        (3, group_portal.id),
                        (3, group_public.id),
                    ]
                })

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._ensure_internal_when_custom_group()
        return users

    def write(self, vals):
        res = super().write(vals)
        self._ensure_internal_when_custom_group()
        return res
