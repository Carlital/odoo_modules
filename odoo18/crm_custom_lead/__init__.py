from . import models
from odoo import api, SUPERUSER_ID


def post_init_stage_baseline(env_or_cr, registry=None):
    """Post-init compatible con firmas de Odoo (env o cr, registry).
    Mantiene activas solo las 4 etapas iniciales; el admin puede aÃ±adir mÃ¡s luego.
    """
    # Detecta si recibimos un Environment o un cursor
    if hasattr(env_or_cr, 'cr') and hasattr(env_or_cr, 'user'):
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    xmlids = [
        'crm_custom_lead.crm_stage_registro',
        'crm_custom_lead.crm_stage_validacion',
        'crm_custom_lead.crm_stage_post_venta',
        'crm_custom_lead.crm_stage_cerrado',
    ]
    keep = []
    for xid in xmlids:
        try:
            keep.append(env.ref(xid).id)
        except Exception:
            continue
    if keep:        
        Stage = env['crm.stage'].sudo()
        if 'active' in Stage._fields:
            Stage.search([('id', 'not in', keep)]).write({'active': False})
        else:
            pass