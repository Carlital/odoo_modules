# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class PeAccount(models.Model):
    _name = 'pe.account'
    _description = 'Peruvian Account'

    date_range_type_id = fields.Many2one('date.range.type', "Date Range Type", required = True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    @api.constrains('company_id')
    def check_company_id(self):
        for pe_account in  self:
            if self.search_count([('company_id','=',pe_account.company_id.id)])>1:
                raise ValidationError(_("Configuration must be unique per Company"))
    
    @api.model
    def get_fiscal_year_id(self, date_from, date_to, company_id):
        fiscal_year_id = self.env['account.fiscal.year'].search([('date_from','=',date_from),('date_to','=',date_to),
                                                                 ('company_id','=',company_id)], limit = 1)
        if not fiscal_year_id:
            vals = {}
            vals['name'] = _("Fiscal Year %s") % fields.Date.from_string(date_from).strftime('%Y')
            vals['date_from'] = date_from
            vals['date_to'] = date_to
            vals['company_id'] = company_id
            fiscal_year_id = self.env['account.fiscal.year'].sudo().create(vals)
        return fiscal_year_id
    
    @api.model
    def get_date_range_type(self, company_id):
        range_type_id = self.env['date.range.type'].search([('company_id','=',company_id)], limit = 1)
        if not range_type_id:
            vals = {}
            vals['name'] =  _("Fiscal Year")
            vals['company_id'] = company_id
            range_type_id = self.env['date.range.type'].sudo().create(vals)
        return range_type_id
    
    @api.model
    def create_date_range(self, date_start, type_id, company_id):
        vals = {}
        vals['name_prefix'] = fields.Date.from_string(date_start).strftime('%Y')
        vals['type_id'] = type_id
        vals['duration_count'] = 1
        vals['unit_of_time'] = '1'
        vals['count'] = 12
        vals['date_start'] = date_start
        vals['company_id'] = company_id
        range_generator_id = self.env['date.range.generator'].sudo().create(vals)
        range_generator_id.action_apply()
        
    
    @api.model
    def create_fiscal_year_from_move(self, move_id):
        vals = {}
        date_from = "%s-01-01" % move_id.date.strftime('%Y')
        date_to = "%s-12-31" % move_id.date.strftime('%Y')
        company_id = move_id.company_id.id
        date_range_type_id = self.get_date_range_type(company_id)
        fiscal_year_id = self.get_fiscal_year_id(date_from, date_to, company_id)
        vals['name'] = _("Fiscal Year %s") % move_id.date.strftime('%Y')
        vals['fiscal_year_id'] = fiscal_year_id.id
        vals['date_range_type_id'] = date_range_type_id.id
        vals['company_id'] = company_id 
        self.sudo().create_date_range(date_from, date_range_type_id, company_id)
        return self.sudo().create(vals)

    @api.model
    def create_fiscal_year_from_le(self, le):
        vals = {}
        date_from = "%s-01-01" % le.start_date.strftime('%Y')
        date_to = "%s-12-31" % le.start_date.strftime('%Y')
        company_id = le.company_id.id
        date_range_type_id = self.get_date_range_type(company_id)
        fiscal_year_id = self.get_fiscal_year_id(date_from, date_to, company_id)
        vals['name'] = _("Fiscal Year %s") % le.start_date.strftime('%Y')
        vals['fiscal_year_id'] = fiscal_year_id.id
        vals['date_range_type_id'] = date_range_type_id.id
        vals['company_id'] = company_id 
        self.sudo().create_date_range(date_from, date_range_type_id, company_id)
        return self.sudo().create(vals)
    
    def create_range_from_pe_accoun(self):
        self.ensure_one()
        date_from = "%s-01-01" % datetime.now().strftime('%Y')
        date_to = "%s-12-31" % datetime.now().strftime('%Y')
        company_id = self.company_id.id
        date_range_type_id = self.get_date_range_type(company_id)
        fiscal_year_id = self.get_fiscal_year_id(date_from, date_to, company_id)
        self.create_date_range(date_from, date_range_type_id, company_id)
        

class PeAccountAbstractReport(models.AbstractModel):
    _name = "pe.account.abstract.le"
    _description = "Electronick Boock Template"
    
    name = fields.Char("Name", copy = False, default='/')
    range_id = fields.Many2one('date.range', 'Range')
    start_date = fields.Date("Start Date", required = True)
    end_date = fields.Date("End Date", required = True)
    state = fields.Selection([('draft', 'Draft'), 
                              ('generated', 'Generated'), ('done', 'Done'), 
                              ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    attachment_id = fields.Many2one('ir.attachment', "Data")
    datas_fname = fields.Char('File Name', compute='_compute_datas', inverse='_inverse_datas')
    datas = fields.Binary(string='File Content', compute='_compute_datas', inverse='_inverse_datas')
    type = fields.Selection([], required = True)
    presentation_code = fields.Selection(selection= "_get_presentation_code", string="Presentation",
                                         help="Código de oportunidad de presentación del EEFF, aplica al Libro de Inventarios y Balances, para los demás consigne '00'")
    operation_code = fields.Selection(selection="_get_operation_code", string="Operation", help="Indicador de operaciones")
    indicator_code = fields.Selection(selection="_get_indicator_code", string="Content", default='1', help="Indicador del contenido del libro o registro")
    currency_code = fields.Selection(selection="_get_currency_code", string="Currency", help="Indicador de la moneda utilizada", default="1")
    sequence_id = fields.Many2one('ir.sequence', 'Sequence')
    number_next = fields.Integer(string='Next Number', default=1)
    prefix = fields.Selection([('A','A'),
                               ('M','M'),
                               ('C','C'),
                               ('M-RER','RER')], "Prefix")
    company_id = fields.Many2one('res.company', string='Company', change_default=True, default=lambda self: self.env.company)
    
    @api.onchange('range_id')
    def _onchage_range_id(self):
        if self.range_id:
            self.start_date = self.range_id.date_start
            self.end_date = self.range_id.date_end
    
    def check_sequence_id(self):
        self.ensure_one()
        sequence_id = self.env['ir.sequence'].sudo().search([('code','=',"pe.sunat.%s" % self.type),('company_id','=',self.company_id.id)], limit = 1)
        if not sequence_id:
            sequence_id = self.set_sequence_id()
        else:
            if sequence_id.prefix != self.prefix:
               sequence_id.prefix = self.prefix
            date_range = self.env['ir.sequence.date_range'].search([('sequence_id', '=', sequence_id.id), ('date_from', '>=', self.start_date), ('date_from', '<=', self.end_date)], order='date_from desc', limit=1)
            date_range.number_next_actual = self.number_next
        return sequence_id
        
    def get_sequence_id(self):
        self.ensure_one()
        return self.check_sequence_id()
    
    def set_sequence_id(self):
        self.ensure_one()
        vals = {}
        vals['name'] = _("Sequence %s") % self.type
        vals['code'] = "pe.sunat.%s" % self.type
        vals['company_id'] = self.company_id.id
        vals['use_date_range'] = True
        vals['range_reset'] = 'monthly'
        vals['prefix'] = self.prefix
        vals['implementation'] = 'no_gap'
        sequence_id = self.env['ir.sequence'].sudo().create(vals)
        return sequence_id
        
    def _get_report_base_filename(self):
        self.ensure_one()
        le = self
        if le.type:
            vals = {}
            vals['ruc'] = le.company_id.vat or ""
            if le.start_date and le.type:
                if le.type[0:2] in ['03']:
                    vals['periodo'] = le.strftime('%Y%m%d')
                else:
                    vals['periodo'] = le.start_date.strftime('%Y%m00')
            else:
                vals['periodo'] = ""
            
            vals['tipo'] = le.type or ""
            vals['presentacion'] = le.presentation_code or ""
            vals['operacion'] = le.operation_code or ""
            vals['indicador'] = le.indicator_code or ""
            vals['moneda'] = le.currency_code or ""
            name = "LE{ruc}{periodo}{tipo}{presentacion}{operacion}{indicador}{moneda}1".format(**vals)
            return name
        else:
            return "Draft"
    
    @api.model
    def _get_presentation_code(self):
        res = []
        res.append(('00','Otros'))
        res.append(('01','Al 31 de diciembre'))
        res.append(('02','Al 31 de enero, por modificación del porcentaje'))
        res.append(('03','Al 30 de junio, por modificación del coeficiente o porcentaje'))
        res.append(('04','Al último día del mes que sustentará la suspensión o modificación del coeficiente (distinto al 31 de enero o 30 de junio)'))
        res.append(('05','Al día anterior a la entrada en vigencia de la fusión, escisión y demás formas de reorganización de sociedades o empresas o extinción de la persona jurídica'))
        res.append(('06','A la fecha del balance de liquidación, cierre o cese definitivo del deudor tributario'))
        res.append(('07','A la fecha de presentación para libre propósito'))
        return res
    
    @api.model
    def _get_operation_code(self):
        res = []
        res.append(('0','Cierre de operaciones - baja de inscripción en el RUC'))
        res.append(('1','Empresa o entidad operativa'))
        res.append(('2','Cierre del libro - no obligado a llevarlo'))
        return res
        
    @api.model
    def _get_indicator_code(self):
        res = []
        res.append(('0','Sin información'))
        res.append(('1','Con información'))
        return res
    
    @api.model
    def _get_currency_code(self):
        res = []
        res.append(('1', 'Soles'))
        res.append(('2', 'US dólares'))
        return res
    
    @api.depends('attachment_id')
    def _compute_datas(self):
        for attach in self:
            if attach.attachment_id:
                attach.datas = attach.attachment_id.datas
                attach.datas_fname = attach.attachment_id.datas_fname

    def _inverse_datas(self):
        for attach in self:
            if attach.datas_fname:
                vals = {
                    'name' : attach.datas_fname,
                    'datas' : attach.datas or b'',
                    'datas_fname' : attach.datas_fname,
                    'type' : 'binary'
                }
                if self.attachment_id:
                    self.attachment_id.write(vals)
                else:
                    attachment_id = self.env['ir.attachment'].create(vals)
                    self.attachment_id = attachment_id
    
    def action_draft(self):
        self.write({'state':'draft'})
    
    def action_generated(self):
        self.write({'state':'generated'})
    
    def action_done(self):
        self.write({'state':'done'})
    
    def action_cancelled(self):
        self.write({'state':'cancelled'})
    