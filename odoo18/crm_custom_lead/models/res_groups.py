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


class ResGroups(models.Model):
    _inherit = 'res.groups'

    def write(self, vals):
        
        if 'users' in vals:
            try:
                custom_group_ids = [self.env.ref(x).id for x in CUSTOM_GROUP_XMLIDS]
            except Exception:
                custom_group_ids = []
            if any(g.id in custom_group_ids for g in self):
                cmds = vals.get('users') or []
                user_ids = set()
                for cmd in cmds:
                    if not isinstance(cmd, (list, tuple)) or not cmd:
                        continue
                    if cmd[0] == 4 and len(cmd) > 1:
                        user_ids.add(cmd[1])
                    elif cmd[0] == 6 and len(cmd) > 2 and isinstance(cmd[2], (list, tuple)):
                        user_ids.update(cmd[2])
                if user_ids:
                    group_user = self.env.ref('base.group_user')
                    group_portal = self.env.ref('base.group_portal')
                    group_public = self.env.ref('base.group_public')
                    users = self.env['res.users'].browse(list(user_ids)).sudo()
                    for u in users:
                        u.write({'groups_id': [
                            (4, group_user.id),
                            (3, group_portal.id),
                            (3, group_public.id),
                        ]})
        res = super().write(vals)
        return res

