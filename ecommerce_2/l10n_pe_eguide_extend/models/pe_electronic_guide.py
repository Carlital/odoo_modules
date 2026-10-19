# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
import requests
from base64 import encodebytes, decodebytes
from odoo.exceptions import UserError, ValidationError
import re
from io import BytesIO
import qrcode
import pytz
from datetime import datetime, timedelta

class PeElectronicGuide(models.Model):
    _name = "pe.electronic.guide"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Electronic Guide"

    # Informacion de Guia Electronica
    name = fields.Char("Name", default="/", copy=False)
    state = fields.Selection([('to_send', 'To Send'), ('generate', 'Generate'), ('to_check', 'To Check'),
                              ('sent', 'Sent'), ('to_cancel', 'To Cancel'), ('cancelled', 'Cancelled')],
                             default='to_send', index=True, readonly=True, track_visibility='onchange')
    reason_transfer = fields.Selection(selection="_get_reason_transfer", string="Reason for Transfer",
                                       states={'to_send': [('readonly', False)]}, readonly=True,
                                       copy=False, required=True)
    country_id = fields.Many2one("res.country", "Country", store=True, compute="_compute_country_id")
    partner_id = fields.Many2one("res.partner", 'Partner', required=True, domain="[('parent_id','=',False)]",
                                 states={'to_send': [('readonly', False)]}, readonly=True,)
    src_state_id = fields.Many2one("res.country.state", string='Source State',
                                   states={'to_send': [('readonly', False)]}, readonly=True,)
    src_province_id = fields.Many2one('res.country.province', string='Source Province',
                                      states={'to_send': [('readonly', False)]}, readonly=True,)
    src_district_id = fields.Many2one('res.country.district', string='Source District',
                                      states={'to_send': [('readonly', False)]}, readonly=True,)
    src_street = fields.Char("Source Street", states={'to_send': [('readonly', False)]}, readonly=True,)

    dst_state_id = fields.Many2one("res.country.state", string='Destination State',
                                   states={'to_send': [('readonly', False)]}, readonly=True,)
    dst_province_id = fields.Many2one('res.country.province', string='Destination Province',
                                      states={'to_send': [('readonly', False)]}, readonly=True,)
    dst_district_id = fields.Many2one('res.country.district', string='Destination District',
                                      states={'to_send': [('readonly', False)]}, readonly=True,)
    dst_street = fields.Char("Destination Street", states={'to_send': [('readonly', False)]}, readonly=True,)

    gross_weight = fields.Float("Gross Weigh", digits=dp.get_precision('Product Unit of Measure'), copy=False,
                                   default=1, states={'to_send': [('readonly', False)]}, readonly=True,)
    unit_quantity = fields.Integer("Unit Quantity", copy=False, default=1, states={'to_send': [('readonly', False)]}, readonly=True,)
    transport_mode = fields.Selection(selection="_get_pe_transport_mode", string="Transport Mode",
                                      copy=False, states={'to_send': [('readonly', False)]}, readonly=True,)

    date_issue = fields.Datetime('Date Issue', copy=False, default=fields.Datetime.now,
                                 states={'to_send': [('readonly', False)]}, readonly=True,)

    transfer_date = fields.Date('Transfer Date', copy=False, default= fields.Date.context_today,
                                states={'to_send': [('readonly', False)]}, readonly=True,)
    vehicle_m1_l = fields.Boolean("Vehicle M1 L", copy=False,
                                  states={'to_send': [('readonly', False)]}, readonly=True,)
    is_programmed = fields.Boolean("Transfer Programmed", copy=False,
                                   states={'to_send': [('readonly', False)]}, readonly=True,)

    description = fields.Char("Guide Description", states={'to_send': [('readonly', False)]}, readonly=True,)

    note = fields.Text("Note", states={'to_send': [('readonly', False)]}, readonly=True,)

    carrier_id = fields.Many2one(comodel_name="res.partner", string="Carrier", copy=False,
                                 states={'to_send': [('readonly', False)]}, readonly=True,)
    vehicle_ids = fields.One2many("pe.electronic.guide.vehicle", "guide_id", "Vehicles",
                                  states={'to_send': [('readonly', False)]}, readonly=True,)
    carrier_ids = fields.One2many("pe.electronic.guide.driver", "guide_id", "Drivers",
                                  states={'to_send': [('readonly', False)]}, readonly=True,)
    related_ids = fields.One2many("pe.electronic.guide.related", "guide_id", "Related Document",
                                  states={'to_send': [('readonly', False)]}, readonly=True,)

    line_ids = fields.One2many("pe.electronic.guide.line", "guide_id", "Lines",
                               states={'to_send': [('readonly', False)]}, readonly=True,)

    user_id = fields.Many2one('res.users', string='User', index=True, track_visibility='onchange', required=True,
                              states={'to_send': [('readonly', False)]}, readonly=True,
                              default=lambda self: self.env.user)
    src_branch_id = fields.Many2one("pe.electronic.guide.branch", "Source Branch",
                                    states={'to_send': [('readonly', False)]}, readonly=True,
                                    domain="[('company_id','=',company_id)]")
    dst_branch_id = fields.Many2one("pe.electronic.guide.branch", "Destination Branch",
                                    states={'to_send': [('readonly', False)]}, readonly=True,
                                    domain="[('company_id','=',company_id)]")
    session_id = fields.Many2one("pe.electronic.guide.session", "Serie", domain="[('company_id','=',company_id)]",
                                 states={'to_send': [('readonly', False)]}, readonly=True,
                                 compute="_compute_session_id", store=True,
                                 required="True")

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 states={'to_send': [('readonly', False)]}, readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get('pe.electronic.guide'))


    # XML y Rpta de SUNAT
    attachment_id = fields.Many2one("ir.attachment", "XML Sign", store=True, readonly=True,
                                       copy=False)
    qr_code = fields.Binary("Qr Code", compute="_compute_qr_code")
    hash_qr = fields.Char("Hash Qr", readonly=True,)
    response_id = fields.Many2one("ir.attachment", "Response File", readonly=True, copy=False)
    response = fields.Char("Response", readonly=True)
    response_note = fields.Text("Note", readonly=True)
    response_return_code = fields.Selection("_get_pe_return_code", string="Return Code", readonly=True)
    digest = fields.Char("Digest", readonly=True)
    ticket = fields.Char("Ticket", readonly=True)
    sent_date = fields.Datetime("Send Date", readonly=True, states={'to_send': [('readonly', False)]})
    date_end = fields.Datetime("End Date", readonly=True, states={'to_send': [('readonly', False)]})

    @api.onchange("src_branch_id", "dst_branch_id")
    def _onchange_branch(self):
        if self.src_branch_id:
            self.src_street = self.src_branch_id.street
            self.src_state_id = self.src_branch_id.state_id.id
            self.src_province_id = self.src_branch_id.province_id.id
            self.src_district_id = self.src_branch_id.district_id.id
        if self.dst_branch_id:
            self.dst_street = self.dst_branch_id.street
            self.dst_state_id = self.dst_branch_id.state_id.id
            self.dst_province_id = self.dst_branch_id.province_id.id
            self.dst_district_id = self.dst_branch_id.district_id.id
    @api.multi
    def action_to_send(self):
        attachment_ids = self.mapped('attachment_id')
        attachment_ids.unlink()
        return self.write({'state': 'to_send'})

    @api.multi
    def action_generate(self):
        for guide_id in self:
            if guide_id.name == '/':
                guide_id.name = guide_id.session_id.sequence_id.next_by_id()
            errors = guide_id._validate_cpe()
            if errors:
                raise ValidationError("\n".join(errors))
            data = self.env['pe.electronic.guide.send'].get_eguide_document(guide_id)
            xml_name = self.get_document_name()
            attachment_id = self.env['ir.attachment'].create({
                'name': "%s.xml" % xml_name,
                'datas_fname': "%s.xml" % xml_name,
                'datas': str(data.get('xml_firmado'), 'utf-8'),
                'mimetype': 'application/xml'
            })
            guide_id.attachment_id = attachment_id.id
            guide_id.digest = data.get('resumen', False)
            guide_id.signature = data.get('firma', False)
            guide_id.hash_qr = data.get('hashqr', False)
        return self.write({'state': 'generate'})

    @api.multi
    def action_sent(self):
        for guide_id in self:
            guide_id.sent_date = fields.Datetime.now()
            if not guide_id.attachment_id:
                guide_id.action_generate()
            data = self.env['pe.electronic.guide.send'].send_eguide_document(guide_id)
            guide_id.ticket = data.get('datos_respuesta', False) or False
            if data.get('respuesta'):
                guide_id._check_response(data.get('respuesta'))
            if guide_id.ticket:
                guide_id.state = 'to_check'
                guide_id.action_document_status()
        self.filtered(lambda cpe: cpe.state not in ['sent']).write({'state': 'to_check'})

    @api.multi
    def action_cancelled(self):
        return self.write({'state': 'cancelled'})

    @api.model
    def _get_pe_return_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

    @api.multi
    @api.depends('user_id', 'company_id')
    def _compute_session_id(self):
        for guide_id in self:
            session_id = False
            if guide_id.user_id and guide_id.company_id:
                query ="""SELECT pe_electronic_guide_session_users_rel.session_id 
                       FROM pe_electronic_guide_session_users_rel INNER JOIN pe_electronic_guide_session 
                       ON pe_electronic_guide_session_users_rel.session_id = pe_electronic_guide_session.id
                       WHERE pe_electronic_guide_session.company_id=%s AND pe_electronic_guide_session_users_rel.user_id=%s
                       LIMIT 1"""
                self.env.cr.execute(query, (guide_id.company_id.id, guide_id.user_id.id))
                session = self.env.cr.dictfetchone()
                session_id = session and session.get('session_id') or False
            guide_id.session_id = session_id

    def _compute_qr_code(self):
        for guide_id in self:
            if guide_id.name:
                qr_string=(guide_id.company_id.pe_eguide_verify_url or "")+ \
                          "v1/contribuyente/gre/comprobantes/descargaqr?hashqr=%s" % guide_id.hash_qr
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
                qr.add_data(qr_string)
                qr.make(fit=True)
                image = qr.make_image()
                tmpf = BytesIO()
                image.save(tmpf,'png')
                guide_id.qr_code = str(encodebytes(tmpf.getvalue()), 'utf-8')

    @api.multi
    def _check_response(self, response):
        self.ensure_one()
        if response.get('codigo'):
            data_id = self.env['pe.datas'].search(
                [('code', '=', response.get('codigo')), ('tanble_code', '=', 'PE.CPE.ERROR')],
                limit=1)
            data_ids = self.env['pe.datas'].search(
                [('table_code', '=', 'PE.CPE.ERROR')])
            if data_id:
                self.response_return_code = response.get('codigo')
        if response.get('respuesta'):
            self.response = response.get('respuesta')
        if response.get('codigo') == '0000':
            self.state = 'sent'
            date_end = fields.Datetime.now()
            self.date_end = date_end
        res = ""
        if response.get('nota'):
            res += "%s\n" % response.get('nota')
        if response.get('faultcode'):
            code = response.get('faultcode', '').split(".")[-1]
            data_id = self.env['pe.datas'].search(
                [('code', '=', code), ('table_code', '=', 'PE.CPE.ERROR')],
                limit=1)
            if data_id:
                self.response_return_code = code
            self.response = response.get('faultcode')
            res += "%s " % response.get('faultcode')
        if response.get('faultstring'):
            res += response.get('faultstring', "")
        if res:
            self.response_note = res
        if response.get("hashqr", False):
            self.hash_qr = response.get("hashqr", False)


    @api.model
    def _get_error_code(self):
        return self.env['pe.datas'].get_selection("PE.CPE.ERROR")

    @api.multi
    def get_document_name(self):
        self.ensure_one()
        ruc = self.company_id.partner_id.doc_number
        doc_code = "09"
        number = self.name
        return "%s-%s-%s" % (ruc, doc_code, number)

    @api.multi
    def action_document_status(self):
        for guide_id in self:
            data = self.env['pe.electronic.guide.send'].get_document_guide_status(guide_id, 'guia')
            if data.get('datos_respuesta'):
                xml_name = guide_id.get_document_name()
                attachment_id = self.env['ir.attachment'].create({
                    'name': "R-%s.zip" % xml_name,
                    'datas_fname': "R-%s.zip" % xml_name,
                    'datas': data.get('datos_respuesta'),
                    'mimetype': 'application/zip'
                })
                guide_id.response_id = attachment_id.id
            if data.get('respuesta'):
                guide_id._check_response(data.get('respuesta'))




    def _check_pe_cpe_response(self, response):
        res = super()._check_pe_cpe_response(response)
        if response.get("hashqr", False):
            res['hash_qr'] = response.get("hashqr", False)
        return res

    @api.model
    def create_from_stock(self, picking_id):
        vals = {}
        vals['picking_ids'] = [(4, picking_id.id)]
        vals['type'] = 'sync'
        vals['company_id'] = picking_id.company_id.id
        res = self.create(vals)
        return res

    def _validate_cpe(self):
        self.ensure_one()
        errors = []
        if not self.line_ids:
            errors.append("Es necesario agregar por lo menos un tiem")
        if self.vehicle_m1_l and not self.transport_mode:
            errors.append(_("It is necessary transport mode"))
        if not self.vehicle_m1_l and self.transport_mode and self.transport_mode == '02':
            self.carrier_id = False
        elif not self.vehicle_m1_l and self.transport_mode and self.transport_mode == '01':
            self.write({'carrier_ids': [(6, 0, [])], 'vehicle_ids':[(6, 0, [])]})
        elif self.vehicle_m1_l:
            self.carrier_id = False
            self.write({'carrier_ids': [(6, 0, [])], 'vehicle_ids':[(6, 0, [])]})
        if not self.partner_id:
            errors.append(_("Customer is required"))
        if self.partner_id.id == self.company_id.partner_id.id and self.reason_transfer not in ["02", "04"]:
            errors.append("Destinatario no debe ser igual al remitente")
        if not self.partner_id.doc_type:
            errors.append(_("Customer type document is required"))
        if not self.partner_id.doc_number:
            errors.append(_("Customer number document is required"))
        if not self.carrier_id.doc_type and self.transport_mode=="01" and not self.vehicle_m1_l:
            errors.append(_("Carrier type document is required for %s") %(self.pe_carrier_id.name or ""))
        if not self.carrier_id.doc_number and self.transport_mode=="01" and not self.vehicle_m1_l:
            errors.append(_("Carrier number document is required for %s") %(self.pe_carrier_id.name or ""))
        if self.transport_mode == "02" and not self.carrier_ids:
            errors.append(_("It is necessary to add a driver"))
        if self.transport_mode=="02" and len(self.carrier_ids)>0:
            for driver_id in self.carrier_ids:
                vals = {
                    'name': driver_id.name,
                    'pe_driver_license': driver_id.driver_license,
                    'doc_type': driver_id.doc_type,
                    'doc_number': driver_id.doc_number
                }
                partner_id = driver_id.driver_id
                if not partner_id:
                    partner_id = self.env['res.partner'].search([('doc_type', '=', driver_id.doc_type),
                                                                 ('doc_number', '=', driver_id.doc_number)], limit=1)
                if partner_id:
                    partner_id.write(vals)
                else:
                    partner_id = self.env['res.partner'].create(vals)
                if not driver_id.driver_id:
                    driver_id.driver_id = partner_id.id
                if not driver_id.doc_type:
                    errors.append(_("Carrier type document is required for %s") %(driver_id.name or ""))
                if not driver_id.doc_number:
                    errors.append(_("Carrier number document is required for %s") %(driver_id.name or ""))
                if not driver_id.driver_license:
                    errors.append(_("Driver's license is required for %s") % (driver_id.name or ""))

        elif self.transport_mode=="02" and len(self.vehicle_ids)==0 and not self.vehicle_m1_l:
            errors.append(_("It is necessary to add a vehicle"))
        timezone = pytz.timezone("America/Lima")
        localtimezone = pytz.timezone("UTC")
        date_issue = fields.Datetime.from_string(self.date_issue).replace(tzinfo=localtimezone)
        if date_issue.astimezone(timezone).date() > fields.Date.from_string(self.transfer_date):
            raise UserError(_("The issue date must be less than the delivery date"))
        if self.reason_transfer == '04':
            if self.partner_id.doc_type != '6':
                errors.append(_("The type of document of the issuer must be RUC"))
        if not self.gross_weight > 0.0:
            errors.append(_("Gross weight must be greater than zero"))
        if self.src_branch_id and self.src_branch_id.district_id.id != self.src_district_id.id:
            errors.append(_("The location of the branch of origin must be the same as the source address"))
        if self.dst_branch_id and self.dst_branch_id.district_id.id != self.dst_district_id.id:
            errors.append(_("The location of the branch of destination must be the same as the destination address"))
        return errors

    @api.onchange("transport_mode")
    def _onchange_transport_mode(self):
        if self.transport_mode == '02':
            self.carrier_id = False

    @api.depends("company_id")
    def _compute_country_id(self):
        for guide_id in self:
            guide_id.country_id = guide_id.company_id.country_id.id

    @api.onchange('session_id', 'reason_transfer')
    def _onchange_session_id(self):
        if self.session_id and self.reason_transfer in ['02', '04', '06', '08']:
            self.src_branch_id = False
            self.dst_branch_id = self.session_id.branch_id.id
        if self.session_id and self.reason_transfer not in ['02', '04', '06', '08']:
            self.src_branch_id = self.session_id.branch_id.id
            self.dst_branch_id = False

    @api.onchange("partner_id", "reason_transfer")
    @api.depends("partner_id", "reason_transfer")
    def _onchange_partner_id(self):
        if self.partner_id and self.reason_transfer in ['02', '04', '06', '08']:
            self.src_state_id = self.partner_id.state_id.id
            self.src_province_id = self.partner_id.province_id.id
            self.src_district_id = self.partner_id.district_id.id
            self.src_street = self.partner_id.street
            self.dst_state_id = self.dst_branch_id.state_id.id or self.company_id.partner_id.state_id.id
            self.dst_province_id = self.dst_branch_id.province_id.id or self.company_id.partner_id.province_id.id
            self.dst_district_id = self.dst_branch_id.district_id.id or self.company_id.partner_id.district_id.id
            self.dst_street = self.dst_branch_id.street or self.company_id.partner_id.street
        elif self.partner_id and self.reason_transfer:
            self.src_state_id = self.src_branch_id.state_id.id or self.company_id.partner_id.state_id.id
            self.src_province_id = self.src_branch_id.province_id.id or self.company_id.partner_id.province_id.id
            self.src_district_id = self.src_branch_id.district_id.id or self.company_id.partner_id.district_id.id
            self.src_street = self.src_branch_id.street or self.company_id.partner_id.street
            self.dst_state_id = self.partner_id.state_id.id
            self.dst_province_id = self.partner_id.province_id.id
            self.dst_district_id = self.partner_id.district_id.id
            self.dst_street = self.partner_id.street
        else:
            self.src_state_id = False
            self.src_province_id = False
            self.src_district_id = False
            self.src_street = False
            self.dst_state_id = False
            self.dst_province_id = False
            self.dst_district_id = False
            self.dst_street = False

    @api.model
    def _get_pe_transport_mode(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG18")

    @api.model
    def _get_reason_transfer(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG20")

    @api.multi
    def get_pe_print_date(self):
        today = fields.Datetime.context_timestamp(self, datetime.now())
        return fields.Datetime.to_string(today)


    @api.model
    def send_async_eguide(self, days=7, limit=30):
        date = fields.Date.to_string(datetime.now() - timedelta(days=days))
        guide_ids = self.search([('date', '>=', date), ('state', 'not in', ['to_send', 'cancelled'])], limit=limit,
                                order='transfer_date ASC')
        for guide_id in guide_ids:
            if not guide_id.ticket:
                guide_id.action_sent()
                if guide_id.ticket:
                    guide_id.env.cr.commit()
            else:
                guide_id.action_document_status()
class PeElectronicGuideLine(models.Model):
    _name = "pe.electronic.guide.line"

    guide_id = fields.Many2one('pe.electronic.guide', "Guide")
    sequence = fields.Integer(default=10,
                              help="Gives the sequence of this line when displaying the invoice.")
    name = fields.Char("Description", required=True)
    product_code = fields.Char("Product Code", required=True)
    barcode = fields.Char('Barcode', copy=False,
                          help="International Article Number used for product identification.")
    uom_code = fields.Selection(selection="_get_uom_code", string="Unit Code", default='NIU', required=True)
    quantity = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), required=True)

    product_id = fields.Many2one("product.product", "Product")

    @api.model
    def _get_uom_code(self):
        return self.env['pe.datas'].get_selection("PE.TABLA06")

    @api.onchange("product_id")
    @api.depends("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.product_code = self.product_id.default_code
            self.uom_code = self.product_id.uom_id.sunat_code or 'NIU'



class PeElectronicGuideRelated(models.Model):
    _name = "pe.electronic.guide.related"
    _description = "Documento Relacionado a la Guia"

    guide_id = fields.Many2one('pe.electronic.guide', "Guide")
    name = fields.Char("Document Number", required=True)
    document_type = fields.Selection(selection="_get_document_type", string="Document Type", required=True)
    partner_id = fields.Many2one("res.partner", 'Partner', required=True)



    @api.model
    def _get_document_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG61")

class PeElectronicGuideVehicle(models.Model):
    _name = "pe.electronic.guide.vehicle"
    _description = "vehicle"

    vehicle_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")
    guide_id = fields.Many2one('pe.electronic.guide', "Guide")
    name = fields.Char("Plate", required=True)
    is_main = fields.Boolean("Main")
    # Entidad emisora de la autorización
    # Número de autorización

    @api.onchange("vehicle_id")
    def onchange_fleet_id(self):
        if self.vehicle_id:
            self.name = self.vehicle_id.license_plate

class PeElectronicGuideDriver(models.Model):
    _name = "pe.electronic.guide.driver"
    _description = "Driver"

    @api.model
    def _get_doc_type(self):
        res = []
        res.append(('0', 'DOC.TRIB.NO.DOM.SIN.RUC'))
        res.append(('1', 'DOCUMENTO NACIONAL DE IDENTIDAD (DNI)'))
        res.append(('4', 'CARNET DE EXTRANJERIA'))
        res.append(('6', 'REGISTRO ÚNICO DE CONTRIBUYENTES'))
        res.append(('7', 'PASAPORTE'))
        res.append(('A', 'CÉDULA DIPLOMÁTICA DE IDENTIDAD'))
        res.append(('B', 'DOC.IDENT.PAIS.RESIDENCIA-NO.D'))
        res.append(('C', 'Tax Identifi cation Number - TIN – Doc Trib PP.NN'))
        res.append(('D', 'Identifi cation Number - IN – Doc Trib PP. JJ'))
        return res

    guide_id = fields.Many2one('pe.electronic.guide', "Guide")
    driver_id = fields.Many2one("res.partner", "Driver")
    name = fields.Char("Name", required=True)
    driver_license = fields.Char("Driver License", required=True)
    doc_type = fields.Selection(selection=_get_doc_type, string="Document Type", required=True)
    doc_number = fields.Char("Document Number", required=True)


    @api.onchange("driver_id")
    @api.depends("driver_id")
    def _onchange_driver_id(self):
        self.name = self.driver_id.name
        self.driver_license = self.driver_id.pe_driver_license
        self.doc_type = self.driver_id.doc_type
        self.doc_number = self.driver_id.doc_number

    @api.onchange("doc_type","doc_number")
    @api.depends("doc_type", "doc_number")
    def _onchange_doc_type_number(self):
        if not self.driver_id and self.doc_type and self.doc_number and self.doc_type=='1':
            vat = self.doc_number
            if len(vat) != 8 and not vat.isdigit():
                warning = {
                    'title': _("Warning for %s") % vat,
                    'message': _('the DNI entered is incorrect')
                }
                return {'warning': warning}

            try:
                response = requests.get("http://api.grupoyacck.com/dni/%s/" % vat.strip(), timeout=300)
            except Exception:
                reponse = False
            if response and response.status_code != 200:
                vals = {'detail': "Not found."}
            else:
                vals = response and response.json() or {'detail': "Not found."}
            if vals.get('detail', '') == "Not found.":
                warning = {
                    'title': _("Warning for %s") % vat,
                    'message': _('Could not get the data')
                }
                return {'warning': warning}
            if vals:
                self.name = "%s %s, %s" % (
                vals.get('paternal_surname', ''), vals.get('maternal_surname', ''), vals.get('name', ''))
