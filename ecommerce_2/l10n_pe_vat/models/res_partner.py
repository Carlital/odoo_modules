# -*- encoding: utf-8 -*-
import requests
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from collections import OrderedDict
import re
import logging
_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    pe_doc_type= fields.Char(string="Document Type", compute="_compute_pe_doc_type_number", store=True)
    pe_doc_number= fields.Char(string="Document Number", compute = "_compute_pe_doc_number")
    pe_commercial_name = fields.Char("Commercial Name", default="-", help='If you do not have a commercial name, put "-" without quotes')
    pe_legal_name = fields.Char("Legal Name", default="-", help='If you do not have a legal name, put "-" without quotes')
    
    pe_state = fields.Selection([('ACTIVO', 'ACTIVO'),
                            ('BAJA DE OFICIO', 'BAJA DE OFICIO'),
                            ('BAJA DEFINITIVA', 'BAJA DEFINITIVA'),
                            ('BAJA PROVISIONAL', 'BAJA PROVISIONAL'),
                            ('SUSPENSION TEMPORAL', 'BAJA PROVISIONAL'),
                            ('INHABILITADO-VENT.UN', 'INHABILITADO-VENT.UN'),
                            ('BAJA MULT.INSCR. Y O', 'BAJA MULT.INSCR. Y O'),
                            ('PENDIENTE DE INI. DE', 'PENDIENTE DE INI. DE'),
                            ('OTROS OBLIGADOS', 'OTROS OBLIGADOS'),
                            ('NUM. INTERNO IDENTIF', 'NUM. INTERNO IDENTIF'),
                            ('ANUL.PROVI.-ACTO ILI', 'ANUL.PROVI.-ACTO ILI'),
                            ('ANULACION - ACTO ILI', 'ANULACION - ACTO ILI'),
                            ('BAJA PROV. POR OFICI', 'BAJA PROV. POR OFICI'),
                            ('ANULACION - ERROR SU', 'ANULACION - ERROR SU')], "Sunat Status", default="ACTIVO")
    pe_condition = fields.Selection([('HABIDO', 'HABIDO'),
                                ('NO HABIDO', 'NO HABIDO'),
                                ('NO HALLADO', 'NO HALLADO'),
                                ('PENDIENTE', 'PENDIENTE'),
                                ('NO HALLADO SE MUDO D', 'NO HALLADO SE MUDO D'),
                                ('NO HALLADO NO EXISTE', 'NO HALLADO NO EXISTE'),
                                ('NO HALLADO FALLECIO', 'NO HALLADO FALLECIO'),
                                ('-', 'NO HABIDO'),
                                ('NO HALLADO OTROS MOT','NO HALLADO OTROS MOT'),
                                ('NO APLICABLE', 'NO APLICABLE'),
                                ('NO HALLADO NRO.PUERT', 'NO HALLADO NRO.PUERT'),
                                ('NO HALLADO CERRADO', 'NO HALLADO CERRADO'),
                                ('POR VERIFICAR', 'POR VERIFICAR'),
                                ('NO HALLADO DESTINATA', 'NO HALLADO DESTINATA'),
                                ('NO HALLADO RECHAZADO', 'NO HALLADO RECHAZADO')], 'Condition', default="HABIDO")

    pe_retention_agent = fields.Boolean("Is Agent")
    pe_retention_agent_from = fields.Date("From")
    pe_retention_agent_resolution = fields.Char("Resolution")
    pe_is_validate= fields.Boolean("Is Validated")
    pe_type_taxpayer = fields.Char("Type Taxpayer")
    pe_emission_system = fields.Char("Emission System")
    pe_accounting_system = fields.Char("Accounting System")
    pe_last_update = fields.Date("Last Update")

    @api.depends('l10n_latam_identification_type_id', 'vat', 'country_id')
    def _compute_pe_doc_type_number(self):
        for partner in self:
            if partner.l10n_latam_identification_type_id:
                if partner.l10n_latam_identification_type_id.l10n_pe_vat_code:
                    partner.pe_doc_type = partner.l10n_latam_identification_type_id.l10n_pe_vat_code
                elif partner.l10n_latam_identification_type_id and partner.l10n_latam_identification_type_id.country_id.code !='PE' and partner.vat:
                    partner.pe_doc_type = '0'
                else:
                    partner.pe_doc_type = False

    @api.depends('vat')
    def _compute_pe_doc_number(self):
        for partner in self:
            partner.pe_doc_number = partner.vat

    def check_vat_pe(self, vat):
        return True      
    
    @api.constrains("vat", "l10n_latam_identification_type_id")
    def check_doc_number(self):
        for partner in self:
            if partner.country_id.code!='PE':
                continue
            vat = partner.vat
            if partner.parent_id:
                continue
            if not partner.l10n_latam_identification_type_id and not vat:
                continue
            if partner.l10n_latam_identification_type_id and not vat:
                continue
            if not partner.l10n_latam_identification_type_id and vat:
                raise ValidationError(_("Select a document type"))
            if partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '6':
                check = self.validate_ruc(vat)
                if not check:
                    _logger.info("The RUC Number [%s] is not valid !" % vat)
                    raise ValidationError(_('The RUC Number [%s] is not valid !') % vat)
            elif partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '0':
                if len(vat)>15 or not vat.isalnum():
                    _logger.info("The OTROS Number [%s] is not valid !" % vat)
                    raise ValidationError(_("The OTROS Number [%s] is not valid !")% vat)
            elif partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                check = self.validate_dni(vat)
                if not check:
                    _logger.info("The DNI Number [%s] is not valid !" % vat)
                    raise ValidationError(_('The DNI Number [%s] is not valid !') % vat)
            elif partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '4':
                if len(vat)>12 or not vat.isalnum():
                    _logger.info("The CARNET DE EXTRANJERIA Number [%s] is not valid !" % vat)
                    raise ValidationError(_('The CARNET DE EXTRANJERIA Number [%s] is not valid !') % vat)
            elif partner.l10n_latam_identification_type_id.l10n_pe_vat_code == '7':
                if len(vat)>12 or not vat.isalnum():
                    _logger.info("The PASAPORTE Number [%s] is not valid !" % vat)
                    raise ValidationError(_('The PASAPORTE Number [%s] is not valid !') %vat)
            elif partner.l10n_latam_identification_type_id.l10n_pe_vat_code == 'A':
                if len(vat)>15 or not vat.isdigit():
                    _logger.info("The CEDULA DIPLOMATICA Number [%s] is not valid !" % vat)
                    raise ValidationError(_('The CEDULA DIPLOMATICA Number [%s] is not valid !') % vat)
            if self.search_count([('l10n_latam_identification_type_id', '=', partner.l10n_latam_identification_type_id.id),
                                  ('vat', '=', partner.vat)])>1:
                if self.env['res.company'].search([('partner_id','!=', partner.id)]):
                    _logger.info('Document Number already exists and violates unique field constrain')
                    raise ValidationError(_('Document Number already exists and violates unique field constrain'))

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.country_id.code=='PE':
            if self.company_type == 'company':
                l10n_latam_identification_type_id = self.env['l10n_latam.identification.type'].search(
                    [('l10n_pe_vat_code', '=', '6')], limit=1)
                self.l10n_latam_identification_type_id = l10n_latam_identification_type_id.id
            else:
                l10n_latam_identification_type_id = self.env['l10n_latam.identification.type'].search(
                    [('l10n_pe_vat_code', '=', '1')], limit=1)
                self.l10n_latam_identification_type_id = l10n_latam_identification_type_id.id
        super(Partner, self).onchange_company_type()
    
    @staticmethod
    def validate_dni(vat):
        if len(vat) != 8:
            return False
        if not vat.isdigit():
            return False
        return True
    
    @staticmethod
    def validate_ruc(vat):
        factor = '5432765432'
        sum = 0
        dig_check = False
        if len(vat) != 11:
            return False
        try:
            int(vat)
        except ValueError:
            return False 
        for f in range(0,10):
            sum += int(factor[f]) * int(vat[f])
        subtraction = 11 - (sum % 11)
        if subtraction == 10:
            dig_check = 0
        elif subtraction == 11:
            dig_check = 1
        else:
            dig_check = subtraction
        if not int(vat[10]) == dig_check:
            return False
        return True
    
    @api.onchange("vat", "l10n_latam_identification_type_id")
    @api.depends("vat", "l10n_latam_identification_type_id")
    def _doc_number_change(self):
        vat = self.vat
        warning = {}
        if vat and self.l10n_latam_identification_type_id:
            vat_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
            if vat_type == '1':
                self.country_id = self.env.ref('base.pe').id
                if len(vat)!=8:
                    warning = {
                            'title': _("Warning for %s") % vat,
                            'message':_('the DNI entered is incorrect')
                        }
                    return {'warning': warning}
                token = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_vat.token')
                vals = self.get_pe_partner_vals_by_doc(vat_type, vat, token)
                if vals and vals.get('detail') != 'Not found.':
                    if vals.get('paternal_surname', '') and vals.get('maternal_surname', '') and vals.get('name', ''):
                        self.name= "%s %s, %s" %(vals.get('paternal_surname', ''), vals.get('maternal_surname', ''), vals.get('name', ''))
                        self.pe_is_validate = True

                self.company_type="person"
            elif vat_type=="6":
                self.country_id = self.env.ref('base.pe').id
                if not self.validate_ruc(vat):
                    warning = {
                            'title': _("Warning for %s") % vat,
                            'message':_('the RUC entered is incorrect')
                        }
                    return {'warning': warning}
                token = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_vat.token')
                vals = self.get_pe_partner_vals_by_doc(vat_type, vat, token)
                if vals.get('detail', '') == "Not found.":
                    warning = {
                            'title': _("Warning for %s") % vat,
                            'message':_('RUC not found, try checking again')
                        }
                    return {'warning': warning}
                if vals:
                    self.pe_commercial_name = vals.get('commercial_name', False)
                    self.pe_legal_name = vals.get('legal_name', False)
                    self.name = vals.get('legal_name') or  vals.get('name') or False
                    self.street = vals.get('street', False)
                    self.company_type="company"
                    self.pe_state = vals.get('state', False)
                    self.pe_condition = vals.get('condition', False)
                    self.pe_type_taxpayer = vals.get('type_taxpayer', False)
                    self.pe_emission_system = vals.get('emission_system', False)
                    self.pe_accounting_system = vals.get('accounting_system', False)
                    try:
                        self.pe_last_update = vals.get('last_update') and fields.Datetime.context_timestamp(self, datetime.strptime(vals.get('last_update'), '%Y-%m-%dT%H:%M:%S.%fZ')) or False
                    except Exception:
                        pass
                    self.pe_is_validate = True
                    self.pe_retention_agent = vals.get('retention_agent', False)
                    self.pe_retention_agent_from = vals.get('retention_agent_from', False)
                    self.pe_retention_agent_resolution = vals.get('retention_agent_resolution', False)
                    if vals.get('ubigeo'):
                        district = self.env['l10n_pe.res.city.district'].search([('code','=', vals.get('ubigeo'))], limit = 1)
                        if district:
                            self.l10n_pe_district=district.id
                            self.city_id = district.city_id.id
                            self.state_id = district.city_id.state_id.id
                            self.country_id = district.city_id.state_id.country_id.id
                            self.zip = vals.get('ubigeo')
                            self.city = district.city_id.name
        return {'warning': warning}

    #def write(self, vals):
    #    return  super(Partner, self).write(vals)
    
    @api.model
    def change_commercial_name(self):
        partner_ids=self.search([('commercial_name', '!=', '-'), ('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', '6')])
        partner_ids.update_document()

    def update_document(self):
        for partner in self:
            partner._doc_number_change()

    @api.model
    def update_partner_datas(self):
        partner_ids = self.search([('l10n_latam_identification_type_id.l10n_pe_vat_code', '=', '6')])
        for partner in partner_ids:
            partner.name = partner.commercial_name

    @staticmethod
    def get_pe_partner_vals_by_doc(doc_type, doc_number, token=False):
        url=None
        res={}
        if token:
            headers = {'Authorization': 'Bearer %s' % token}
        else:
            headers = {}
        if doc_type=="1":
            url = "https://api.mifactura.digital/v2/dni/%s/" % doc_number
        elif doc_type=="6":
            url = "https://api.mifactura.digital/v2/ruc/%s/" % doc_number
        if url:
            try:
                response = requests.get(url, headers=headers)
            except Exception:
                reponse=False
            if response and response.status_code==200:
                vals = response and response.json() or {'detail':"Not found."}
                res = vals
        return res

    @api.model
    def get_partner_from_ui(self, doc_type=None, doc_number=None):
        token = self.env['ir.config_parameter'].sudo().get_param('l10n_pe_vat.token')
        res = self.get_pe_partner_vals_by_doc(doc_type, doc_number, token)
        if res.get('ubigeo'):
            district = self.env['l10n_pe.res.city.district'].search([('code','=', res.get('ubigeo'))], limit=1)
            if district:
                res['l10n_pe_district']=district.id
                res['city_id'] = district.city_id.id
                res['state_id'] = district.city_id.state_id.id
                res['city'] = district.name
            if res.get('ubigeo') and res.get('ubigeo') != '-':
                res['zip'] = res.get('ubigeo')
        if res:
            res['country_id'] = self.env.ref('base.pe').id
        return res
