# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import requests
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)
class acs_pos_partner_search(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_partners(self, query):
        if query.isdigit():
            # Search by doc_number first (Peruvian localization), then fallback to vat
            doc_number_field = 'doc_number' in self._fields
            if doc_number_field:
                partners = self.env['res.partner'].search([('doc_number', 'ilike', query),('customer_rank','!=',0)], limit=10)
            else:
                partners = self.env['res.partner'].search([('vat', 'ilike', query),('customer_rank','!=',0)], limit=10)
        else:
            partners = self.env['res.partner'].search([('name', 'ilike', query),('customer_rank','!=',0)], limit=10)
        if partners:
            partner_data = {}
            for partner in partners:
                address = (partner.street or '') +', '+ (partner.zip or '')    +' '+(partner.city or '')   +', '+ (partner.country_id.name or '')
                barcode = partner.barcode or ''
                city = partner.city or ''
                country_id = [partner.country_id.id, partner.country_id.name] if partner.country_id else []
                partner_data.update({partner.id:{'id': partner.id, 'name': partner.name,'address':address,'barcode':barcode,'city':city,'country_id':country_id,'email':partner.email,'phone':partner.phone,'mobile':partner.mobile,'vat':partner.vat}})
            return partner_data
        else:
            return False

    @api.model
    def get_by_doc_number(self,doc_number):
        _logger.info("[ACS POS Partner Search] get_by_doc_number called with doc_number: %s", doc_number)
        vat=doc_number
        partner_data = {}

        if vat and vat.isdigit():
            _logger.info("[ACS POS Partner Search] doc_number is digit, length: %s", len(vat))
            has_doc_type = 'doc_type' in self._fields
            if len(vat) == 8:
                vat_type = '1'
                vals = None

                if hasattr(self, 'get_pe_partner_vals_by_doc'):
                    try:
                        token = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_vat.token')
                        vals = self.get_pe_partner_vals_by_doc(vat_type, vat, token)
                    except Exception:
                        vals = None

                if not vals or vals.get('detail') == 'Not found.':
                    try:
                        response = requests.get("http://api.grupoyacck.com/dni/%s/" % vat.strip(), timeout = 300)
                        if response and response.status_code==200:
                            vals = response.json()
                        else:
                            vals = {'detail': "Not found."}
                    except Exception:
                        vals = {'detail': "Not found."}

                if vals:
                    name= "%s %s, %s" %(vals.get('paternal_surname', ''), vals.get('maternal_surname', ''), vals.get('name', ''))
                    company_type="person"
                    is_validate = True

                    dni_type = self.env.ref('l10n_pe.it_DNI', raise_if_not_found=False)
                    if dni_type:
                        partner_data.update({'l10n_latam_identification_type_id': dni_type.id})

                    peru_country = self.env.ref('base.pe', raise_if_not_found=False)
                    if peru_country:
                        partner_data.update({'country_id': peru_country.id})

                    if has_doc_type:
                        partner_data.update({'doc_type':vat_type})
                    partner_data.update({'name':name,'doc_number':vat,'vat':vat,'company_type':company_type,'is_validate':is_validate})
                    partner_data.update({'customer_rank':1})
            elif len(vat) == 11:
                _logger.info("[ACS POS Partner Search] Processing RUC with 11 digits: %s", vat)
                vat_type = '6'
                # Validate RUC format if validation method exists
                if hasattr(self, 'validate_ruc'):
                    _logger.info("[ACS POS Partner Search] validate_ruc method exists, validating...")
                    try:
                        if not self.validate_ruc(vat):
                            _logger.warning("[ACS POS Partner Search] RUC validation failed for: %s", vat)
                            return {'state':302,'msg':f'El RUC {vat} ingresado es incorrecto'}
                        _logger.info("[ACS POS Partner Search] RUC validation passed")
                    except Exception as e:
                        _logger.warning("[ACS POS Partner Search] Exception during RUC validation: %s", str(e))
                        pass  # Continue if validation fails

                try:
                    url = "http://api.grupoyacck.com/ruc/%s/" % vat.strip()
                    if self.env.context.get('force_update'):
                        url = "http://api.grupoyacck.com/ruc/%s/?force_update=1" % vat.strip()
                    _logger.info("[ACS POS Partner Search] Calling SUNAT API: %s", url)
                    response = requests.get(url, timeout=300)
                    _logger.info("[ACS POS Partner Search] SUNAT API response status: %s", response.status_code)
                except Exception as exc:
                    _logger.exception("Error calling SUNAT API for %s: %s", doc_number, exc)
                    return {'state':302,'msg':f'Error al buscar el cliente con el numero {doc_number} !'}

                # Check response status
                if response and response.status_code != 200:
                    _logger.warning("[ACS POS Partner Search] SUNAT API returned non-200 status: %s", response.status_code)
                    vals = {'detail': "Not found."}
                else:
                    vals = response and response.json() or {'detail':"Not found."}
                    _logger.info("[ACS POS Partner Search] SUNAT API response data: %s", vals)

                # Check if SUNAT returned valid data
                if vals.get('detail') == 'Not found.':
                    _logger.warning("[ACS POS Partner Search] SUNAT did not find RUC: %s", doc_number)
                    return {'state':302,'msg':f'No se ha encontrado un RUC con el numero {doc_number} en SUNAT'}

                commercial_name_field = 'commercial_name' in self._fields
                legal_name_field = 'legal_name' in self._fields
                if vals:
                    commercial_name = vals.get('commercial_name')
                    legal_name = vals.get('legal_name')
                    name = vals.get('legal_name') or  vals.get('legal_name') 
                    street = vals.get('street', False)
                    company_type="company"
                    state = vals.get('state', False)
                    condition = vals.get('condition')
                    type_taxpayer = vals.get('type_taxpayer')
                    emission_system = vals.get('emission_system')
                    accounting_system = vals.get('accounting_system')
                    last_update = vals.get('last_update') and fields.Datetime.context_timestamp(self, datetime.strptime(vals.get('last_update'), '%Y-%m-%dT%H:%M:%S.%fZ')) or False
                    is_validate = True
                    data_to_store = {'name':name,'doc_number':vat,'street':street,'company_type':company_type,'state':state,'condition':condition,'type_taxpayer':type_taxpayer,'emission_system':emission_system,'accounting_system':accounting_system,'last_update':last_update,'is_validate':is_validate}
                    if commercial_name_field:
                        data_to_store['commercial_name'] = commercial_name
                    if legal_name_field:
                        data_to_store['legal_name'] = legal_name
                    if has_doc_type:
                        data_to_store['doc_type'] = vat_type

                    ruc_type = self.env.ref('l10n_pe.it_RUC', raise_if_not_found=False)
                    if ruc_type:
                        data_to_store['l10n_latam_identification_type_id'] = ruc_type.id

                    peru_country = self.env.ref('base.pe', raise_if_not_found=False)
                    if peru_country:
                        data_to_store['country_id'] = peru_country.id

                    partner_data.update(data_to_store)
                    if vals.get('activities'):
                        activities_ids = []
                        for activity in  vals.get('activities'):
                            ciiu = self.env['pe.datas'].search([('code', '=', activity.get('code')),('table_code', '=', 'PE.CIIU')], limit=1)
                            if ciiu:
                                activities_ids.append(ciiu.id)
                            else:
                                activity['table_code']='PE.CIIU'
                                ciiu = self.env['pe.datas'].sudo().create(activity)
                                activities_ids.append(ciiu.id)
                        if activities_ids:
                            main_activity = activities_ids[-1]
                            partner_data.update({'main_activity':main_activity})
                            act=[]
                            for activity_id in activities_ids:
                                act.append((4,activity_id))
                            partner_data.update({'activity_ids':act})
                    if vals.get('representatives'):
                        representatives=[]
                        for rep in vals.get('representatives'):
                            representatives.append((0, None,rep))
                        representative_ids = representatives
                        partner_data.update({'representative_ids':representative_ids})
                    retention_agent = vals.get('retention_agent', False)
                    retention_agent_from = vals.get('retention_agent_from', False)
                    retention_agent_resolution = vals.get('retention_agent_resolution', False)
                    partner_data.update({'retention_agent':retention_agent,'retention_agent_from':retention_agent_from,'retention_agent_resolution':retention_agent_resolution})
                    if vals.get('district') and vals.get('province'):
                        district = self.env['res.country.district'].search([('name','ilike', vals.get('district')),
                                                                               ('province_id.name','ilike', vals.get('province'))])
                        if len(district)==1:
                            district_id=district.id
                            partner_data.update({'district_id':district_id})
                        elif len(district)==0:
                            province = self.env['res.country.province'].search([('name','ilike', vals.get('province'))])
                            if len(province)==1:
                                province_id=province.id
                                partner_data.update({'province_id':province_id})
                        else:
                            province = self.env['res.country.province'].search([('name','ilike', vals.get('province'))])
                            if len(province)==1:
                                province_id=province.id
                                partner_data.update({'province_id':province_id})
                # For RUC: store VAT without prefix (constraint expects 11 digits)
                partner_data.update({'customer_rank':1})
                partner_data.update({'vat':vat})
            if partner_data:
                _logger.info("[ACS POS Partner Search] Partner data collected, processing...")
                partner_vals = dict(partner_data)
                doc_number_value = partner_vals.pop('doc_number', False)
                _logger.info("[ACS POS Partner Search] doc_number_value: %s", doc_number_value)
                doc_number_field = 'doc_number' in self._fields
                if doc_number_value and doc_number_field:
                    partner_vals['doc_number'] = doc_number_value

                # Store VAT without prefix - constraint expects clean format (11 digits for RUC, 8 for DNI)
                if doc_number_value:
                    partner_vals.setdefault('vat', doc_number_value)
                partner_vals.setdefault('customer_rank', 1)

                _logger.info("[ACS POS Partner Search] Final VAT value: %s", partner_vals.get('vat'))

                domain = []
                if doc_number_value and doc_number_field:
                    domain.append(('doc_number', '=', doc_number_value))
                elif partner_vals.get('vat'):
                    domain.append(('vat', '=', partner_vals['vat']))

                _logger.info("[ACS POS Partner Search] Search domain: %s", domain)

                allowed_keys = set(self._fields.keys())
                partner_vals = {key: value for key, value in partner_vals.items() if key in allowed_keys}
                _logger.info("[ACS POS Partner Search] Filtered partner_vals keys: %s", list(partner_vals.keys()))

                existing_partner = domain and self.env['res.partner'].search(domain, limit=1)
                if existing_partner:
                    _logger.info("[ACS POS Partner Search] Updating existing partner: %s (id=%s)", existing_partner.name, existing_partner.id)
                    existing_partner.write(partner_vals)
                    partner_record = existing_partner
                    action_msg = f"Se ha actualizado el cliente {partner_record.name}"
                else:
                    _logger.info("[ACS POS Partner Search] Creating new partner...")
                    partner_record = self.env['res.partner'].create(partner_vals)
                    _logger.info("[ACS POS Partner Search] New partner created: %s (id=%s)", partner_record.name, partner_record.id)
                    action_msg = f"Se ha registrado el cliente {partner_record.name}"

                _logger.info("[ACS POS Partner Search] Returning success with partner_id: %s", partner_record.id)
                return {'state':200,'msg':action_msg,'partner_id':partner_record.id}
            _logger.warning("[ACS POS Partner Search] No partner data collected")
            return {'state':302,'msg':f'No se ha encontra un cliente con el numero {doc_number} !'}
        else:
            _logger.warning("[ACS POS Partner Search] doc_number is not digit: %s", doc_number)
            return {'state':302,'msg':f'Porfavor verificar el numero {doc_number} !'}

