from odoo import http, _
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class N8nImportController(http.Controller):

    @http.route('/crm_custom_campaign_ext/n8n/import_plans', type='json', auth='public', csrf=False, methods=['POST'])
    def import_plans(self, **kw):
        # --- 1) Auth por Bearer ---
        expected = request.env['ir.config_parameter'].sudo().get_param('crm_custom_campaign_ext.n8n_token')
        auth = (request.httprequest.headers.get('Authorization') or '').strip()
        token = auth.replace('Bearer ', '').strip()
        if not expected or token != expected:
            return {'status': 'error', 'message': 'unauthorized'}

        # --- 2) Cuerpo JSON real (n8n manda application/json plano) ---
        body = request.get_json_data(silent=True) or request.jsonrequest or {}
        # por compatibilidad, si algún día llega algo en kw
        if not body and kw:
            body = kw

        plans = body.get('plans') or []
        if not isinstance(plans, list):
            return {'status': 'error', 'message': 'invalid payload (plans should be list)'}

        meta = body.get('meta') or {}
        meta_subcampaign = meta.get('subcampaign_id')

        # --- 3) Modelos con sudo ---
        Plan = request.env['bc.plan'].sudo()
        PlanLine = request.env['bc.plan.line'].sudo()
        Currency = request.env['res.currency'].sudo()
        Subcampaign = request.env['bc.subcampaign'].sudo()
        Icon = request.env['bc.icon'].sudo() if 'bc.icon' in request.env.registry.models else None

        created = 0
        updated = 0
        errors = []

        for idx, p in enumerate(plans):
            try:
                name = (p.get('name') or '').strip()
                if not name:
                    continue

                external = p.get('external_id')
                if external and 'x_external_id' in Plan._fields:
                    domain = [('x_external_id', '=', external)]
                else:
                    domain = [('name', '=', name)]

                plan = Plan.search(domain, limit=1)

                vals = {
                    'name': name,
                    'sequence': p.get('sequence', 10),
                    'headline': p.get('headline') or False,
                    'price_no_tax': p.get('price_no_tax') or 0.0,
                    'price_with_tax': p.get('price_with_tax') or 0.0,
                }

                # Subcampaña: del propio plan o de meta.subcampaign_id
                sub_id = p.get('subcampaign_id') or meta_subcampaign
                if sub_id:
                    sc = None
                    if isinstance(sub_id, int):
                        sc = Subcampaign.search([('id', '=', sub_id)], limit=1)
                    else:
                        sc = Subcampaign.search([('name', '=', str(sub_id))], limit=1)
                    if sc:
                        vals['subcampaign_id'] = sc.id

                # Moneda por nombre o símbolo
                cur_code = p.get('currency')
                if cur_code:
                    cur = Currency.search([('name', '=', cur_code)], limit=1) or \
                          Currency.search([('symbol', '=', cur_code)], limit=1)
                    if cur:
                        vals['currency_id'] = cur.id

                if external and 'x_external_id' in Plan._fields:
                    vals['x_external_id'] = external

                if plan:
                    plan.write(vals)
                    if hasattr(plan, 'line_ids'):
                        plan.line_ids.sudo().unlink()
                    updated += 1
                else:
                    plan = Plan.create(vals)
                    created += 1

                # Líneas
                for ln in (p.get('lines') or []):
                    lvals = {
                        'plan_id': plan.id,
                        'sequence': ln.get('sequence', 10),
                        'titulo': ln.get('titulo') or '',
                        'detalle': ln.get('detalle') or '',
                    }
                    icon_key = ln.get('icon_key')
                    if icon_key and Icon:
                        icon = Icon.search([('name', '=', icon_key)], limit=1) or \
                               Icon.search([('code', '=', icon_key)], limit=1)
                        if icon:
                            lvals['icon_id'] = icon.id
                    PlanLine.create(lvals)

            except Exception as e:
                _logger.exception('Error processing plan at index %s', idx)
                errors.append({'index': idx, 'error': str(e)})

        return {'status': 'ok', 'created': created, 'updated': updated, 'errors': errors}
