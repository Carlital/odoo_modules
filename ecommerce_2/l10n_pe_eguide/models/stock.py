# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re
from io import BytesIO
from base64 import encodebytes
import qrcode
try:
    qr_mod = True
except:
    qr_mod = False

class Picking(models.Model):
    _inherit = "stock.picking"
    
    #pe_voided_id = fields.Many2one("pe.eguide", "Guide canceled", copy=False)
    pe_guide_number = fields.Char("Guide Number", default="/", copy=False)
    pe_is_realeted = fields.Boolean("Is Related", copy=False)
    pe_related_number = fields.Char("Related Number", copy=False)
    pe_related_code = fields.Selection(selection="_get_pe_related_code", string="Related Number", copy=False)
    pe_supplier_id = fields.Many2one(comodel_name="res.partner", string="Supplier", copy=False)
    pe_transfer_code = fields.Selection(selection="_get_pe_transfer_code", string="Transfer code", default="01", copy=False)
    pe_gross_weight = fields.Float("Gross Weigh", digits='Product Unit of Measure', copy=False, default=1.0)
    pe_unit_quantity = fields.Integer("Unit Quantity", copy=False, default=1)
    pe_transport_mode = fields.Selection(selection="_get_pe_transport_mode", string="Transport Mode", copy=False)
    pe_carrier_id = fields.Many2one(comodel_name="res.partner", string="Carrier", compute="_compute_pe_carrier_id", inverse="_inverse_pe_carrier_id")
    pe_is_eguide = fields.Boolean("Is EGuide", copy=False)
    pe_is_programmed = fields.Boolean("Transfer Programmed", copy=False)
    pe_date_issue = fields.Datetime('Date Issue', copy=False)
    pe_fleet_ids = fields.One2many(comodel_name="pe.stock.fleet", inverse_name="picking_id", string="Fleet Private", copy=False)
    
    pe_guide_ids = fields.One2many("pe.eguide", 'picking_id', "Guides Electronic", copy=False)
    
    pe_guide_id = fields.Many2one("pe.eguide", "Guide Electronic", compute = "_compute_pe_eguide_detail", store=True, copy=False)
    pe_digest = fields.Char("Digest", compute = "_compute_pe_eguide_detail", store=True, copy=False)
    pe_response = fields.Char("Response", compute = "_compute_pe_eguide_detail", store=True, copy=False)
    pe_return_code = fields.Selection("_get_return_code", string= "Return Code",  compute="_compute_pe_eguide_detail", store=True, copy=False)
    pe_note = fields.Char(string= "Return Code",  compute="_compute_pe_eguide_detail", store=True, copy=False)
    pe_response_id = fields.Many2one("ir.attachment", "XML", compute="_compute_pe_eguide_detail", store=True, copy=False)
    pe_attachment_id = fields.Many2one("ir.attachment", "XML Response", compute="_compute_pe_eguide_detail", store=True, copy=False)
    
    pe_qr_code = fields.Binary("Qr Code", compute="_compute_pe_qr_code")
    
    pe_return_code = fields.Selection("_get_return_code", string= "Return Code",  readonly=True)
    pe_carrier_ids = fields.Many2many('res.partner', 'stock_picking_pe_carrier_rel', 'stock_id', 'partner_id', "Carriers", copy=False)

    pe_other_street = fields.Boolean("Add Other Street", copy=False)
    pe_country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
                                    copy=False, compute = "_compute_other_street", store=True, readonly = False)
    pe_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', pe_country_id)]", copy=False,
                                  compute = "_compute_other_street", store=True, readonly = False)
    pe_city_id = fields.Many2one('res.city', string='City of Address', domain="[('state_id', '=?', pe_state_id)]", copy=False,
                                 compute = "_compute_other_street", store=True, readonly = False)
    l10n_pe_district = fields.Many2one('l10n_pe.res.city.district', string='District', domain="[('city_id', '=?', pe_city_id)]",
                                       compute = "_compute_other_street", store=True, readonly = False,
                                       help='Districts are part of a province or city.', copy=False)
    pe_street = fields.Char("Street", copy=False)
    pe_warehouse_id = fields.Many2one('stock.warehouse', 'Eguide Warehouse', compute="_compute_pe_warehouse_id")

    pe_transfer_date = fields.Date('Transfer Date', copy=False)
    pe_vehicle_m1_l = fields.Boolean("Vehicle M1 L", copy=False)
    pe_related_ids = fields.One2many("pe.stock.related", inverse_name="picking_id", string="Carriers")
    pe_description = fields.Char("Guide Description", compute="compute_pe_description",
                                 inverse="inverse_pe_description")

    def action_reset_electronic_guide(self):
        self.ensure_one()
        self.pe_date_issue = False
        self.pe_guide_number = '/'
        self.pe_guide_ids.write({'picking_id': False})
        return {}

    @api.depends("partner_id")
    def _compute_other_street(self):
        for stock_id in self:
            if stock_id.partner_id:
                stock_id.pe_country_id  = stock_id.partner_id.country_id.id
                stock_id.pe_state_id = stock_id.partner_id.state_id.id
                stock_id.pe_city_id = stock_id.partner_id.city_id.id
                stock_id.l10n_pe_district = stock_id.partner_id.l10n_pe_district.id
                stock_id.pe_street = stock_id.partner_id.street
            else:
                stock_id.pe_country_id = self.env.company.country_id.id
                stock_id.pe_state_id = False
                stock_id.pe_city_id = False
                stock_id.l10n_pe_district = False
                stock_id.pe_street = False

    def guide_print(self):
        self.ensure_one()
        if not self.pe_guide_id.hash_qr_url and self.pe_guide_id.pe_ticket:
            self.pe_guide_id.action_document_status()
        if not self.pe_guide_id.hash_qr_url:
            raise UserError(_("The QR code is not available"))
        return self.env.ref('l10n_pe_eguide.action_report_eguide').report_action(self)

    @api.depends('origin')
    def compute_pe_description(self):
        for picking_id in self:
            picking_id.pe_description = picking_id.origin

    def inverse_pe_description(self):
        for picking_id in self:
            picking_id.origin = picking_id.pe_description


    #@api.depends("location_id", "company_id", "picking_type_id")
    def _compute_pe_warehouse_id(self):
        for picking_id in self:
            location_id = picking_id.picking_type_id.code in ['outgoing', 'internal'] and picking_id.location_id.id or picking_id.location_dest_id.id
            warehouse_id = self.env['stock.warehouse'].search([("company_id","=",picking_id.picking_type_id.company_id.id),
                                                               ("lot_stock_id","=", location_id)], limit=1)
            if not warehouse_id:
                warehouse_id = self.env['stock.warehouse'].search([("company_id", "=", picking_id.picking_type_id.company_id.id),
                                                                   ("wh_input_stock_loc_id", "=", location_id)],
                                                                  limit=1)
            if not warehouse_id:
                warehouse_id = self.env['stock.warehouse'].search([("company_id", "=", picking_id.picking_type_id.company_id.id),
                                                                   ("wh_qc_stock_loc_id", "=", location_id)],
                                                                  limit=1)
            if not warehouse_id:
                warehouse_id = self.env['stock.warehouse'].search([("company_id", "=", picking_id.picking_type_id.company_id.id),
                                                                   ("wh_pack_stock_loc_id", "=",  location_id)],
                                                                  limit=1)
            if not warehouse_id:
                warehouse_id = self.env['stock.warehouse'].search([("company_id", "=", picking_id.picking_type_id.company_id.id),
                                                                   ("wh_output_stock_loc_id", "=", location_id)],
                                                                  limit=1)
            if not warehouse_id:
                warehouse_id = picking_id.picking_type_id.warehouse_id
            picking_id.pe_warehouse_id = warehouse_id.id

    @api.depends('pe_guide_ids.pe_digest',
                 'pe_guide_ids.pe_response',
                 'pe_guide_ids.pe_return_code',
                 'pe_guide_ids.pe_response_id',
                 'pe_guide_ids.attachment_id')
    def _compute_pe_eguide_detail(self):
        for picking_id in self:
            pe_guide_ids = picking_id.pe_guide_ids
            pe_guide_id = pe_guide_ids and pe_guide_ids[0] or False
            picking_id.pe_guide_id = pe_guide_id and pe_guide_id[0] or False
            picking_id.pe_digest = pe_guide_id and  pe_guide_id.pe_digest or False
            picking_id.pe_response = pe_guide_id and  pe_guide_id.pe_response or False
            picking_id.pe_return_code = pe_guide_id and pe_guide_id.pe_return_code or False
            picking_id.pe_response_id = pe_guide_id and pe_guide_id.pe_response_id.id or False
            picking_id.pe_attachment_id = pe_guide_id and pe_guide_id.attachment_id.id or False
            picking_id.pe_note = pe_guide_id and pe_guide_id.pe_note or False
    
    @api.depends('pe_carrier_ids','pe_transport_mode')
    def _compute_pe_carrier_id(self):
        for stock_id in self:
            pe_carrier_id = False
            for pe_carrier in stock_id.pe_carrier_ids:
                pe_carrier_id = pe_carrier.id
                break
            stock_id.pe_carrier_id = pe_carrier_id
            
    @api.depends('pe_carrier_id','pe_transport_mode')
    def _inverse_pe_carrier_id(self):
        for stock_id in self:
            if stock_id.pe_transport_mode in ['01']:
                stock_id.pe_carrier_ids = [(6,0,stock_id.pe_carrier_id.ids)]
    
    @api.model
    def _get_return_code(self):
        return self.env['pe.catalog.return'].get_selection()
    
    @api.model
    def _get_pe_transport_mode(self):
        return self.env['pe.catalog.18'].get_selection()
    
    @api.model
    def _get_pe_related_code(self):
        return self.env['pe.catalog.21'].get_selection()

    @api.model
    def _get_pe_transfer_code(self):
        return self.env['pe.catalog.20'].get_selection()
    
    def action_cancel_eguide(self):
        for picking_id in self:
                if picking_id.pe_guide_id and picking_id.pe_guide_id.state not in ["draft", "generate", "cancel"]:
                    voided_id = self.env['pe.eguide'].get_eguide_async('low', picking_id)
                    picking_id.pe_voided_id = voided_id.id
    
    def _compute_pe_qr_code(self):
        for picking_id in self:
            res=[]
            if picking_id.pe_guide_number and picking_id.pe_is_eguide and qr_mod and picking_id.pe_guide_id.hash_qr_url:
                qr_string = picking_id.pe_guide_id.hash_qr_url
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_Q)
                qr.add_data(qr_string)
                qr.make(fit=True)
                image = qr.make_image()
                tmpf = BytesIO()
                image.save(tmpf,'png')
                picking_id.pe_qr_code = encodebytes(tmpf.getvalue())
            else:
                picking_id.pe_qr_code = False

    def do_new_transfer(self):
        res=super(Picking, self).do_new_transfer()
        self.pe_gross_weight=sum([line.product_id.weight for line in self.pack_operation_ids])
        self.pe_unit_quantity= sum([line.qty_done or line.product_qty for line in self.pack_operation_ids])
        return res

    def validate_eguide(self):
        self.ensure_one()
        if self.pe_vehicle_m1_l:
            self.pe_carrier_ids = [(6,0, [])]
            self.pe_fleet_ids.unlink()
        if not self.partner_id:
            raise UserError(_("Customer is required"))
        if self.partner_id.id == self.company_id.partner_id.id and self.pe_transfer_code in ["02", "04"]:
            raise UserError("Destinatario no debe ser igual al remitente")
        if not self.partner_id.parent_id.pe_doc_type and not self.partner_id.pe_doc_type:
            raise UserError(_("Customer type document is required"))
        if not self.partner_id.parent_id.pe_doc_number and not self.partner_id.pe_doc_number:
            raise UserError(_("Customer number document is required"))
        if not self.partner_id.street and not self.partner_id.street:
                raise UserError(_("Customer street is required for %s") %(self.partner_id.name or ""))
        if not self.partner_id.l10n_pe_district and not self.l10n_pe_district:
                raise UserError(_("Customer district is required for %s")  %(self.partner_id.name or ""))
        if not self.pe_carrier_id.pe_doc_type and self.pe_transport_mode=="01" and not self.pe_vehicle_m1_l:
            raise UserError(_("Carrier type document is required for %s") %(self.pe_carrier_id.name or ""))
        if not self.pe_carrier_id.pe_doc_number and self.pe_transport_mode=="01" and not self.pe_vehicle_m1_l:
            raise UserError(_("Carrier number document is required for %s") %(self.pe_carrier_id.name or ""))
        if not self.pe_warehouse_id.partner_id or not self.pe_warehouse_id.partner_id.street:
            raise UserError(_("It is necessary to enter the warehouse address for %s") %(self.pe_warehouse_id.partner_id.name or ""))
        if self.pe_warehouse_id.partner_id and not self.pe_warehouse_id.partner_id.l10n_pe_district:
            raise UserError(_("It is necessary to enter the warehouse district for %s") %(self.pe_warehouse_id.partner_id.name or ""))
        if self.pe_transport_mode=="02" and not self.pe_carrier_ids and not self.pe_vehicle_m1_l:
            raise UserError(_("It is necessary to add a driver"))
        if self.pe_carrier_ids:
            for partner_id in self.pe_carrier_ids:
                if not partner_id.pe_doc_type:
                    raise UserError(_("Carrier type document is required for %s") %(partner_id.name or ""))
                if not partner_id.pe_doc_number:
                    raise UserError(_("Carrier number document is required for %s") %(partner_id.name or ""))
                if not partner_id.pe_driver_license and self.pe_transport_mode=="02":
                    raise UserError(_("Carrier driver license is required for %s") %(partner_id.name or ""))
        if not self.pe_vehicle_m1_l and self.pe_transport_mode=="02" and not self.pe_fleet_ids:
            raise UserError(_("It is necessary to add a vehicle and driver"))
        if self.pe_vehicle_m1_l and self.company_id.pe_ws_server == 'nubefact_pse':
            raise UserError(_("Not supported by Nubefact"))
        if self.pe_carrier_ids.filtered(lambda s: s.id == self.company_id.partner_id.id) and self.pe_transport_mode=="01":
            raise UserError("Transportista no debe ser igual al remitente")

    def action_generate_eguide(self):
        for stock in self:
            if stock.pe_is_eguide:
                stock.validate_eguide()
                if not stock.pe_date_issue:
                    stock.pe_date_issue = fields.Datetime.now()
                if stock.pe_guide_number=='/':
                    if stock.pe_warehouse_id.pe_sequence_id:
                        stock.pe_guide_number=stock.pe_warehouse_id.pe_sequence_id.next_by_id()
                    else:
                        stock.pe_guide_number = self.env['ir.sequence'].next_by_code('pe.eguide.sync')
                if not stock.pe_guide_number:
                    raise UserError("No se pudo generar las Secuencia para GRE")
                if not re.match(r'^(T){1}[A-Z0-9]{3}\-\d+$', stock.pe_guide_number):
                    raise UserError("El numero de la guia ingresada no cumple con el estandar.\n"\
                                    "Verificar la secuencia del Diario por jemplo T001- o TG01-. \n"\
                                    "Para cambiar ir a Configuracion/Gestion de Almacenes/Almacenes")
                #if not self.pe_guide_id:
                pe_guide_id = self.env['pe.eguide'].create_from_stock(stock)
                #    stock.pe_guide_id = pe_guide_id.id
                #else:
                #    pe_guide_id=stock.pe_guide_id
                pe_guide_id.action_sent()
                #self.pe_number = stock.pe_guide_number    

class PeStockFleet(models.Model):
    _name = "pe.stock.fleet"
    
    name = fields.Char("License Plate", required=True)
    fleet_id = fields.Many2one(comodel_name="fleet.vehicle", string="Vehicle")
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Picking")
    #driver_id = fields.Many2one(comodel_name="res.partner", string="Driver", required=True)
    is_main = fields.Boolean("Main")
    
    @api.onchange("fleet_id")
    def onchange_fleet_id(self):
        if self.fleet_id:
            self.name = self.fleet_id.license_plate
            #self.driver_id = self.fleet_id.driver_id.id


class PeStockRelated(models.Model):
    _name = "pe.stock.related"
    _description = "Documento Relacionado a la Guia"

    picking_id = fields.Many2one(comodel_name="stock.picking", string="Picking")
    name = fields.Char("Document Number")
    document_type = fields.Selection(selection="_get_document_type", string="Document Type")
    partner_id = fields.Many2one('res.partner', string="Partner")

    @api.model
    def _get_document_type(self):
        return self.env['pe.catalog.61'].get_selection()

class Warehouse(models.Model):
    _inherit = "stock.warehouse"
    
    pe_sequence_id = fields.Many2one('ir.sequence', 'Eguide Sequence', )
