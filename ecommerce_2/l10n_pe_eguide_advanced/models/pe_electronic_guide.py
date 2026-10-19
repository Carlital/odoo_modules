# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
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
    _inherit = ['portal.mixin', 'mail.thread.main.attachment', 'mail.activity.mixin']
    _description = "Electronic Guide"

    # Informacion de Guia Electronica
    name = fields.Char("Name", default="/", copy=False, tracking=True)
    state = fields.Selection([('to_send', 'To Send'), ('generate', 'Generate'), ('to_check', 'To Check'),
                              ('sent', 'Sent'), ('to_cancel', 'To Cancel'), ('cancelled', 'Cancelled')],
                             default='to_send', index=True, readonly=True, tracking=True)
    reason_transfer = fields.Selection(selection="_get_reason_transfer", string="Reason for Transfer")
    country_id = fields.Many2one("res.country", "Country", store=True, compute="_compute_country_id")
    partner_id = fields.Many2one("res.partner", 'Partner', required=True, domain="[('parent_id','=',False)]")
    src_state_id = fields.Many2one("res.country.state", string='Source State')
    src_province_id = fields.Many2one('res.city', string='Source Province')
    src_district_id = fields.Many2one('l10n_pe.res.city.district', string='Source District')
    src_street = fields.Char("Source Street")

    dst_state_id = fields.Many2one("res.country.state", string='Destination State')
    dst_province_id = fields.Many2one('res.city', string='Destination Province')
    dst_district_id = fields.Many2one('l10n_pe.res.city.district', string='Destination District')
    dst_street = fields.Char("Destination Street")

    gross_weight = fields.Float("Gross Weigh", digits='Product Unit of Measure', copy=False,
                                   default=1)
    gross_weight_unit = fields.Selection(selection="_get_gross_weight_unit", string="Gross Weight Unit", default='KGM', copy=False)
    unit_quantity = fields.Integer("Unit Quantity", copy=False, default=1)
    transport_mode = fields.Selection(selection="_get_pe_transport_mode", string="Transport Mode", copy=False)

    date_issue = fields.Datetime('Date Issue', copy=False, default=fields.Datetime.now)

    transfer_date = fields.Date('Transfer Date', copy=False, default= fields.Date.context_today)
    vehicle_m1_l = fields.Boolean("Vehicle M1 L", copy=False)
    is_programmed = fields.Boolean("Transfer Programmed", copy=False)

    description = fields.Char("Guide Description")

    note = fields.Text("Note")

    carrier_id = fields.Many2one(comodel_name="res.partner", string="Carrier")
    register_number = fields.Char("MTC Register Number", compute="_compute_register_number", inverse="_inverse_register_number")
    vehicle_ids = fields.One2many("pe.electronic.guide.vehicle", "guide_id", "Vehicles")
    # main_vehicle_id = fields.Many2one("pe.electronic.guide.vehicle", "Main Vehicle", compute="_compute_vehicles")
    # other_vehicle_ids = fields.Many2many("pe.electronic.guide.vehicle", string="Other Vehicles", compute="_compute_vehicles")
    carrier_ids = fields.One2many("pe.electronic.guide.driver", "guide_id", "Drivers")
    # main_carrier_id = fields.Many2one("pe.electronic.guide.driver", string="Main Driver", compute="_compute_carriers")
    # other_carrier_ids = fields.Many2many("pe.electronic.guide.driver", string="Other Drivers", compute="_compute_carriers")
    related_ids = fields.One2many("pe.electronic.guide.related", "guide_id", "Related Document")

    line_ids = fields.One2many("pe.electronic.guide.line", "guide_id", "Lines")

    user_id = fields.Many2one('res.users', string='User', index=True, required=True,
                              default=lambda self: self.env.user)
    src_branch_id = fields.Many2one("pe.electronic.guide.branch", "Source Branch",
                                    domain="[('company_id','=',company_id)]")
    dst_branch_id = fields.Many2one("pe.electronic.guide.branch", "Destination Branch",
                                    domain="[('company_id','=',company_id)]")
    session_id = fields.Many2one("pe.electronic.guide.session", "Serie", domain="[('company_id','=',company_id)]",
                                 compute="_compute_session_id", store=True)

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self.env.company)


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
    sent_date = fields.Datetime("Send Date", readonly=True)
    date_end = fields.Datetime("End Date", readonly=True)
    hash_qr_url = fields.Char("Hash Qr Url", readonly=True)

    @api.depends("carrier_id")
    def _compute_register_number(self):
        for guide_id in self:
            guide_id.register_number = guide_id.carrier_id.pe_guide_adv_register_number

    def _inverse_register_number(self):
        for guide_id in self:
            if guide_id.carrier_id:
                guide_id.carrier_id.pe_guide_adv_register_number = guide_id.register_number

    @api.model
    def _get_gross_weight_unit(self):
        return self.env['pe.table.06'].get_selection([('code','in',['KGM','TNE'])])

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

    def action_to_send(self):
        attachment_ids = self.mapped('attachment_id')
        attachment_ids.unlink()
        return self.write({'state': 'to_send'})


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
                'datas': str(data.get('xml_firmado'), 'utf-8'),
                'mimetype': 'application/xml'
            })
            guide_id.attachment_id = attachment_id.id
            guide_id.digest = data.get('resumen', False)
            # guide_id.signature = data.get('firma', False)
            guide_id.hash_qr = data.get('hashqr', False)
            guide_id.hash_qr_url = data.get('documento', False)
        return self.write({'state': 'generate'})


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


    def action_cancelled(self):
        return self.write({'state': 'cancelled'})

    @api.model
    def _get_pe_return_code(self):
        return self.env['pe.catalog.return'].get_selection()


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
            if guide_id.name != '/':
                if guide_id.hash_qr_url:
                    qr_string = guide_id.hash_qr_url
                else:
                    qr_string=(guide_id.company_id.pe_eguide_verify_url or "")+ \
                              "v1/contribuyente/gre/comprobantes/descargaqr?hashqr=%s" % guide_id.hash_qr
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
                qr.add_data(qr_string)
                qr.make(fit=True)
                image = qr.make_image()
                tmpf = BytesIO()
                image.save(tmpf,'png')
                guide_id.qr_code = str(encodebytes(tmpf.getvalue()), 'utf-8')
            else:
                guide_id.qr_code = False


    def _check_response(self, response):
        self.ensure_one()
        if response.get('codigo'):
            data_id = self.env['pe.catalog.return'].search(
                [('code', '=', response.get('codigo'))],
                limit=1)
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
            data_id = self.env['pe.catalog.return'].search(
                [('code', '=', code)],
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
        return self.env['pe.catalog.return'].get_selection()


    def get_document_name(self):
        self.ensure_one()
        ruc = self.company_id.partner_id.vat
        doc_code = "09"
        number = self.name
        return "%s-%s-%s" % (ruc, doc_code, number)


    def action_document_status(self):
        for guide_id in self:
            data = self.env['pe.electronic.guide.send'].get_document_guide_status(guide_id, 'guia')
            if data.get('datos_respuesta'):
                xml_name = guide_id.get_document_name()
                attachment_id = self.env['ir.attachment'].create({
                    'name': "R-%s.zip" % xml_name,
                    # 'datas_fname': "R-%s.zip" % xml_name,
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
        if not re.match(r'^(T){1}[A-Z0-9]{3}\-\d+$', self.name):
            errors.append("El número de guía no es válido")
        if not self.line_ids:
            errors.append("Es necesario agregar por lo menos un tiem")
        if self.line_ids.filtered(lambda r: not r.product_id):
            errors.append("Es necesario agregar un producto")
        if self.line_ids.filtered(lambda r: r.quantity <= 0.0):
            errors.append("La cantidad debe ser mayor a cero")
        if self.vehicle_m1_l and not self.transport_mode:
            errors.append(_("It is necessary transport mode"))
        if not self.vehicle_m1_l and self.transport_mode and self.transport_mode == '02':
            self.carrier_id = False
        elif not self.vehicle_m1_l and self.transport_mode and self.transport_mode == '01':
            self.write({'carrier_ids': [(6, 0, [])], 'vehicle_ids':[(6, 0, [])]})
        elif self.vehicle_m1_l:
            # self.carrier_id = False
            self.write({'carrier_ids': [(6, 0, [])], 'vehicle_ids':[(6, 0, [])]})
        if not self.partner_id:
            errors.append(_("Customer is required"))
        if self.partner_id.id == self.company_id.partner_id.id and self.reason_transfer not in ["02", "04", "18"]:
            errors.append("Destinatario no debe ser igual al remitente")
        if not self.partner_id.pe_doc_type:
            errors.append(_("Customer type document is required"))
        if not self.partner_id.vat:
            errors.append(_("Customer number document is required"))
        if not self.carrier_id.pe_doc_type and self.transport_mode=="01" and not self.vehicle_m1_l:
            errors.append(_("Carrier type document is required for %s") %(self.carrier_id.name or ""))
        if not self.carrier_id.vat and self.transport_mode=="01" and not self.vehicle_m1_l:
            errors.append(_("Carrier number document is required for %s") %(self.carrier_id.name or ""))
        if self.transport_mode == "02" and not self.carrier_ids:
            errors.append(_("It is necessary to add a driver"))
        # if self.transport_mode=="02" and len(self.carrier_ids)>0:
        for driver_id in self.carrier_ids:
            l10n_latam_identification_type_id = self.env['l10n_latam.identification.type'].search([('l10n_pe_vat_code', '=', driver_id.doc_type)], limit=1)
            vals = {
                'name': driver_id.name,
                'pe_guide_adv_driver_license': driver_id.driver_license,
                'l10n_latam_identification_type_id': l10n_latam_identification_type_id.id,
                'vat': driver_id.doc_number
            }
            partner_id = driver_id.driver_id
            if not partner_id:
                partner_id = self.env['res.partner'].search([('pe_doc_type', '=', driver_id.doc_type),
                                                             ('vat', '=', driver_id.doc_number)], limit=1)
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

        if self.transport_mode=="02" and len(self.vehicle_ids)==0 and not self.vehicle_m1_l:
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

    # @api.onchange("transport_mode")
    # def _onchange_transport_mode(self):
    #     if self.transport_mode == '02':
    #         self.carrier_id = False

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

    def _change_partner_id(self, partner_id):
        if partner_id and self.reason_transfer in ['02', '04', '06', '08']:
            self.src_state_id = partner_id.state_id.id
            self.src_province_id = partner_id.city_id.id
            self.src_district_id = partner_id.l10n_pe_district.id
            self.src_street = partner_id.street
            self.dst_state_id = self.dst_branch_id.state_id.id or self.company_id.partner_id.state_id.id
            self.dst_province_id = self.dst_branch_id.province_id.id or self.company_id.partner_id.city_id.id
            self.dst_district_id = self.dst_branch_id.district_id.id or self.company_id.partner_id.l10n_pe_district.id
            self.dst_street = self.dst_branch_id.street or self.company_id.partner_id.street
        elif partner_id and self.reason_transfer:
            self.src_state_id = self.src_branch_id.state_id.id or self.company_id.partner_id.state_id.id
            self.src_province_id = self.src_branch_id.province_id.id or self.company_id.partner_id.city_id.id
            self.src_district_id = self.src_branch_id.district_id.id or self.company_id.partner_id.l10n_pe_district.id
            self.src_street = self.src_branch_id.street or self.company_id.partner_id.street
            self.dst_state_id = partner_id.state_id.id
            self.dst_province_id = partner_id.city_id.id
            self.dst_district_id = partner_id.l10n_pe_district.id
            self.dst_street = partner_id.street
        else:
            self.src_state_id = False
            self.src_province_id = False
            self.src_district_id = False
            self.src_street = False
            self.dst_state_id = False
            self.dst_province_id = False
            self.dst_district_id = False
            self.dst_street = False

    @api.onchange("partner_id", "reason_transfer")
    @api.depends("partner_id", "reason_transfer")
    def _onchange_partner_id(self):
        self._change_partner_id(self.partner_id)

    @api.model
    def _get_pe_transport_mode(self):
        return self.env['pe.catalog.18'].get_selection()

    @api.model
    def _get_reason_transfer(self):
        return self.env['pe.catalog.20'].get_selection()

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

    def _get_name_electronic_guide_report(self):
        self.ensure_one()
        if self.company_id.pe_guide_report_template == 'custom':
            return "l10n_pe_eguide_advanced.report_pe_eguide_advanced_document_custom"
        elif self.company_id.pe_guide_report_template == 'stylized':
            return "l10n_pe_eguide_advanced.report_pe_eguide_advanced_document_stylized"
        return "l10n_pe_eguide_advanced.report_pe_eguide_advanced_document_standard"

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
    quantity = fields.Float('Quantity', digits='Product Unit of Measure', required=True)

    product_id = fields.Many2one("product.product", "Product")
    invoice_line_ids = fields.Many2many("account.move.line", "pe_electronic_guide_line_invoice_rel", string="Invoice Lines")
    stock_move_ids = fields.Many2many("stock.move", "pe_electronic_guide_line_stock_move_rel", string="Stock Moves")

    @api.model
    def _get_uom_code(self):
        return self.env['pe.table.06'].get_selection()

    @api.onchange("product_id")
    @api.depends("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.product_code = self.product_id.default_code
            self.uom_code = self.product_id.uom_id.pe_unit_code or 'NIU'



class PeElectronicGuideRelated(models.Model):
    _name = "pe.electronic.guide.related"
    _description = "Documento Relacionado a la Guia"

    guide_id = fields.Many2one('pe.electronic.guide', "Guide")
    name = fields.Char("Document Number", required=True)
    document_type = fields.Selection(selection="_get_document_type", string="Document Type", required=True)
    partner_id = fields.Many2one("res.partner", 'Partner', required=True)



    @api.model
    def _get_document_type(self):
        return self.env['pe.catalog.61'].get_selection()

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
    # register_number = fields.Char("MTC Register Number")


    @api.onchange("driver_id")
    @api.depends("driver_id")
    def _onchange_driver_id(self):
        self.name = self.driver_id.name
        self.driver_license = self.driver_id.pe_guide_adv_driver_license
        self.doc_type = self.driver_id.pe_doc_type
        self.doc_number = self.driver_id.vat

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
