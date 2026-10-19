from odoo import http, _
from odoo.http import request, Response
import logging
import json
import re

_logger = logging.getLogger(__name__)


class N8nImportController(http.Controller):

    @http.route('/crm_custom_campaign_ext/n8n/import_plans', type='http', auth='public', csrf=False, methods=['POST'])
    def import_plans(self, **kw):
        # LOG: headers + raw body for debugging
        try:
            raw_body = request.httprequest.get_data(as_text=True)
        except Exception:
            raw_body = '<unreadable>'
        _logger.info('n8n import_plans called. Headers=%s RawBody=%s', dict(request.httprequest.headers), raw_body[:2000])

        # Parsear JSON tolerante (n8n puede enviar estructuras distintas)
        data = None
        try:
            data = request.httprequest.get_json(force=False, silent=True)
        except Exception:
            data = None

        if data is None:
            # intentar cargar raw text como JSON
            try:
                data = json.loads(raw_body) if raw_body else {}
            except Exception:
                data = {}

        # Si la carga devolvió una cadena JSON dentro del JSON, intentar parsearla
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                pass

        # Si n8n envía una lista (a veces devuelve [obj]), normalizar
        if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
            data = data[0]

        # Si está anidado en keys comunes, intentar normalizar
        if isinstance(data, dict):
            if 'body' in data and isinstance(data['body'], (str, dict)):
                try:
                    body_val = data['body']
                    if isinstance(body_val, str):
                        body_val = json.loads(body_val)
                    if isinstance(body_val, dict):
                        # preferir body.plans si existe
                        if 'plans' in body_val:
                            data = body_val
                except Exception:
                    pass
            if 'data' in data and isinstance(data['data'], dict) and 'plans' in data['data']:
                data = data['data']

        # Finalmente, si el payload es una lista de planes (no envuelve en {"plans": ...})
        plans = []
        if isinstance(data, dict):
            # caso común: {"plans": [...]}
            if 'plans' in data and isinstance(data['plans'], list):
                plans = data['plans']
            # si el dict ya es un plan (tiene name/headline/external_id/subcampaign_id) -> convertir a lista de 1
            elif any(k in data for k in ('name', 'headline', 'external_id', 'subcampaign_id')):
                plans = [data]
            else:
                # fallback: buscar la primera lista cuyo primer elemento parezca un plan (tiene name/headline/external_id)
                for k, v in data.items():
                    if isinstance(v, list) and v and isinstance(v[0], dict) and any(pk in v[0] for pk in ('name', 'headline', 'external_id')):
                        plans = v
                        break
        elif isinstance(data, list) and all(isinstance(x, dict) and ('name' in x or 'sequence' in x) for x in data):
            # ya es una lista de planes
            plans = data

        _logger.info('n8n import_plans parsed plans_count=%s', len(plans) if plans is not None else 0)

        payload = data or {}

        # 1) Autenticación simple por token Bearer
        expected = request.env['ir.config_parameter'].sudo().get_param('crm_custom_campaign_ext.n8n_token')
        auth = request.httprequest.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '').strip()
        if not expected or token != expected:
            body = {'status': 'error', 'message': 'unauthorized'}
            _logger.warning('n8n import_plans unauthorized. provided_token=%s expected_set=%s', bool(token), bool(expected))
            return Response(json.dumps(body), status=401, content_type='application/json')

        if not isinstance(plans, list):
            body = {'status': 'error', 'message': 'invalid payload, no plans array found'}
            _logger.warning('n8n import_plans invalid payload: %s', type(data))
            return Response(json.dumps(body), status=400, content_type='application/json')

        # Logear resumen de los primeros planes para depuración
        for i, p in enumerate(plans[:5]):
            try:
                _logger.info('n8n plan[%s] name=%s external=%s keys=%s', i, p.get('name'), p.get('external_id'), list(p.keys()))
            except Exception:
                _logger.debug('n8n plan[%s] debug failure', i)

        # 2) Preparar modelos (sudo para evitar fallos de permisos en webhook)
        Plan = request.env['bc.plan'].sudo()
        PlanLine = request.env['bc.plan.line'].sudo()
        Currency = request.env['res.currency'].sudo()
        Subcampaign = request.env['bc.subcampaign'].sudo()
        # don't treat a model recordset as boolean — keep model reference and check is None
        IconModel = request.env['bc.icon'] if 'bc.icon' in request.env.registry.models else None

        created = 0
        updated = 0
        errors = []

        for idx, p in enumerate(plans):
            try:
                name = (p.get('name') or '').strip()
                if not name:
                    _logger.debug('Skipping plan at index %s because name empty', idx)
                    continue

                external = p.get('external_id')
                # idempotencia: preferir buscar por campo x_external_id si existe en el modelo
                domain = []
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

                # Subcampaign: accept numeric id or name
                sub_id = p.get('subcampaign_id') or p.get('subcampaign_external_id') or p.get('subcampaign_name')
                if sub_id:
                    sc = None
                    if isinstance(sub_id, int):
                        sc = Subcampaign.search([('id', '=', sub_id)], limit=1)
                    else:
                        sc = Subcampaign.search([('name', '=', str(sub_id))], limit=1)
                    if sc:
                        vals['subcampaign_id'] = sc.id

                # Currency by name/code
                cur_code = p.get('currency')
                if cur_code:
                    cur = Currency.search([('name', '=', cur_code)], limit=1)
                    if not cur:
                        cur = Currency.search([('symbol', '=', cur_code)], limit=1)
                    if cur:
                        vals['currency_id'] = cur.id

                if external and 'x_external_id' in Plan._fields:
                    vals['x_external_id'] = external

                if plan:
                    plan.write(vals)
                    # remove lines to recreate (simple approach)
                    if hasattr(plan, 'line_ids'):
                        plan.line_ids.sudo().unlink()
                    updated += 1
                else:
                    plan = Plan.create(vals)
                    created += 1

                try:
                    attrs = p.get('attributes') or p.get('attributes_list') or []
                    # mapa attr_code -> icon_id (garantiza que un mismo icono no se asigne a >1 atributo)
                    attr_icon_map = {}
                    attr_icon_used = set()
                    attr_icon_names = set()

                    AttrModel = None
                    ValModel = None
                    for m in ('bc.attribute', 'bc.plan.template.attr'):
                        if m in request.env.registry.models:
                            AttrModel = request.env[m].sudo()
                            break
                    for vm in ('bc.plan.value', 'bc.plan.attribute', 'bc.plan.attr', 'bc.plan.attr.value'):
                        if vm in request.env.registry.models:
                            ValModel = request.env[vm].sudo()
                            break

                    if ValModel is None:
                        _logger.warning('n8n: no value model found to store attributes (tried common names)')

                    # detectar nombre del campo many2one que referencia al atributo maestro (si ValModel existe)
                    val_attr_field = None
                    if ValModel:
                        for fname, f in ValModel._fields.items():
                            comodel = getattr(f, 'comodel_name', None)
                            if comodel in ('bc.attribute', 'bc.plan.attribute', 'bc.plan.template.attr'):
                                val_attr_field = fname
                                break
                        if not val_attr_field:
                            for candidate_field in ('attribute_id', 'attribute_line_id', 'plan_attribute_id', 'attribute_tmpl_id'):
                                if candidate_field in ValModel._fields:
                                    val_attr_field = candidate_field
                                    break

                    # AttrModel puede ser None: en ese caso solo intentamos mapear iconos/lines, no crear atributos
                    if isinstance(attrs, list) and attrs:
                        for a in attrs:
                            code = (a.get('code') or a.get('name') or '').strip()
                            if not code:
                                continue

                            # localizar o crear atributo maestro si existe modelo
                            attr_rec = None
                            if AttrModel:
                                attr_rec = AttrModel.search([('code', '=', code)], limit=1) or AttrModel.search([('name', '=', code)], limit=1)
                                if not attr_rec:
                                    try:
                                        attr_rec = AttrModel.create({
                                            'name': code,
                                            'code': code[:64],
                                            'data_type': a.get('type') or 'char',
                                        })
                                    except Exception:
                                        _logger.exception('n8n: failed creating bc.attribute for code=%s', code)
                                        attr_rec = None
                            else:
                                _logger.debug('n8n: AttrModel not available, skipping attribute creation: %s', code)

                            # detección de icon similar al código anterior (si IconModel existe)
                            try:
                                if IconModel is None:
                                    _logger.debug('n8n: bc.icon model not available (IconModel is None)')
                                else:
                                    candidates = set()
                                    c0 = str(code).strip() if code else ''
                                    candidates.update({
                                        c0.lower(),
                                        c0.lower().replace('_', ' '),
                                        c0.lower().replace(' ', '_'),
                                        c0.lower().replace('-', ' ')
                                    })
                                    raw = a.get('value')
                                    if isinstance(raw, (str, int, float)):
                                        raw_s = str(raw)
                                        tokens = [t.strip() for t in re.split(r'[,\s;|]+', raw_s) if t.strip()]
                                        for tk in tokens:
                                            tkl = tk.lower()
                                            candidates.update({
                                                tkl,
                                                tkl.replace('_', ' '),
                                                tkl.replace(' ', '_'),
                                                tkl.replace('-', ' ')
                                            })
                                    for cand in sorted(candidates):
                                        if not cand:
                                            continue
                                        try:
                                            dom_parts = []
                                            if 'code' in IconModel._fields:
                                                dom_parts.append(('code', 'ilike', cand))
                                            dom_parts.append(('name', 'ilike', cand))
                                            domain = ['|', dom_parts[0], dom_parts[1]] if len(dom_parts) == 2 else dom_parts
                                            icon = IconModel.sudo().search(domain, limit=1)
                                        except Exception:
                                            icon = None
                                        if icon and icon.id not in attr_icon_used:
                                            attr_icon_map[code] = icon.id
                                            attr_icon_used.add(icon.id)
                                            attr_icon_names.add(icon.name.strip().lower())
                                            _logger.info('n8n: detected icon=%s for attribute=%s candidate=%s', icon.name, code, cand)
                            except Exception:
                                _logger.exception('n8n: error detecting icons in attribute value for plan %s attr %s', name, code)

                            # crear/actualizar valor del plan si tenemos modelo y campo detectado
                            if ValModel and attr_rec and val_attr_field:
                                vdomain = [(val_attr_field, '=', attr_rec.id), ('plan_id', '=', plan.id)]
                                vrec = ValModel.search(vdomain, limit=1)
                                dtype = (a.get('type') or '').lower()
                                raw = a.get('value')
                                vvals = {'plan_id': plan.id, val_attr_field: attr_rec.id}
                                if dtype in ('float', 'numeric', 'number', 'int'):
                                    try:
                                        vvals['value_float'] = float(str(raw).replace(',', '.')) if raw is not None and str(raw).strip() != '' else None
                                    except Exception:
                                        vvals['value_char'] = str(raw or '')
                                elif dtype in ('boolean', 'bool'):
                                    try:
                                        vvals['value_bool'] = str(raw or '').strip().lower() not in ('0', 'false', 'no', 'n', '')
                                    except Exception:
                                        vvals['value_bool'] = False
                                elif dtype in ('text',):
                                    vvals['value_text'] = str(raw or '')
                                else:
                                    vvals['value_char'] = str(raw or '')

                                try:
                                    if vrec:
                                        vrec.sudo().write(vvals)
                                    else:
                                        ValModel.create(vvals)
                                except Exception:
                                    _logger.exception('n8n: error creating/updating value for plan %s attribute %s', plan and plan.name, code)
                except Exception:
                    _logger.exception('n8n: error processing attributes for plan %s', plan and plan.name)

                # Lines
                for ln in (p.get('lines') or []):
                    lvals = {
                        'plan_id': plan.id,
                        'sequence': ln.get('sequence', 10),
                        'titulo': ln.get('titulo') or '',
                        'detalle': ln.get('detalle') or '',
                    }
                    icon_key = ln.get('icon_key')
                    if icon_key and IconModel is not None:
                        icon = IconModel.sudo().search([('name', '=', icon_key)], limit=1) or IconModel.sudo().search([('code', '=', icon_key)], limit=1)
                        if icon:
                            # set whichever field exists on PlanLine
                            if 'icon_id' in PlanLine._fields:
                                lvals['icon_id'] = icon.id
                            if 'icon_ids' in PlanLine._fields:
                                lvals['icon_ids'] = [(6, 0, [icon.id])]
                    else:
                        # si no hay icon_key en la línea, primero intentar asignar icon por título a partir del mapa de atributos detectados
                        try:
                            titulo = (ln.get('titulo') or '').strip().lower()
                            assigned_ids = []
                            # buscar coincidencia entre título y códigos de atributos detectados
                            if titulo and attr_icon_map:
                                for a_code, a_icon_id in attr_icon_map.items():
                                    # coincidencia sencilla: título contiene código o viceversa (normalizados)
                                    ac_norm = str(a_code or '').strip().lower()
                                    if not ac_norm:
                                        continue
                                    if ac_norm in titulo or titulo in ac_norm:
                                        assigned_ids.append(a_icon_id)
                                        # no romper: puede haber varias coincidencias válidas, pero iconos ya son únicos por atributo
                            # si no encontramos por atributo, intentar coincidencia directa por título en bc.icon
                            if not assigned_ids and IconModel is not None and titulo:
                                try:
                                    if 'code' in IconModel._fields:
                                        found = IconModel.sudo().search([('code', '=', titulo)], limit=1) or IconModel.sudo().search([('name', 'ilike', titulo)], limit=1)
                                    else:
                                        found = IconModel.sudo().search([('name', 'ilike', titulo)], limit=1)
                                except Exception:
                                    found = None
                                if found:
                                    assigned_ids.append(found.id)

                            # asignar solo los ids encontrados para esta línea (sin duplicados)
                            if assigned_ids:
                                ids = list(dict.fromkeys(assigned_ids))
                                if 'icon_ids' in PlanLine._fields:
                                    lvals['icon_ids'] = [(6, 0, ids)]
                                elif 'icon_id' in PlanLine._fields and len(ids) == 1:
                                    lvals['icon_id'] = ids[0]
                        except Exception:
                            _logger.exception('n8n: error assigning icon to plan line for plan %s', plan and plan.name)
                    PlanLine.create(lvals)

            except Exception as e:
                _logger.exception('Error processing plan at index %s', idx)
                errors.append({'index': idx, 'error': str(e)})

        _logger.info('n8n import_plans result created=%s updated=%s errors=%s', created, updated, len(errors))
        body = {'status': 'ok', 'created': created, 'updated': updated, 'errors': errors}
        return Response(json.dumps(body), status=200, content_type='application/json')
