from odoo import models, fields, api
from datetime import datetime, timedelta
import random
import string

class PosToken(models.Model):
    _name = 'pos.token'
    _inherit = ["pos.load.mixin"]
    _description = 'POS Token'

    token = fields.Char(
        string='Token',
        required=True,
        readonly=True,
        copy=False,
        default=lambda self: self._generate_token()
    )

    date_start = fields.Datetime(
        string='Fecha de Inicio',
        default=lambda self: fields.Datetime.now()
    )

    date_end = fields.Datetime(
        string='Fecha de Fin',
        default=lambda self: fields.Datetime.now() + timedelta(minutes=10)
    )

    active = fields.Boolean(
        string='Activo',
        default=True,
        readonly=True
    )

    product_ids = fields.Many2many(
        string='Productos',
        comodel_name='product.product',
        relation='pos_token_product_product_rel',
        column1='product_id',
        column2='token_id',
    )
    
    @api.model
    def _generate_token(self):
        digits = ''.join(random.choices(string.digits, k=4))
        letters = ''.join(random.choices(string.ascii_uppercase, k=2))
        return digits + letters

    @api.model
    def get_token_with_price(self,product_id):
        token = self.search([('active','=',True),('date_start','<=',datetime.now()),('date_end','>=',datetime.now()),('product_ids','in',[product_id])])
        if token:
            return True
        else:
            return False
    @api.model
    def is_valid_token(self,token_str,accion):
        token = self.search([('token','=',token_str),('active','=',True),('date_start','<=',datetime.now()),('date_end','>=',datetime.now())])
        if accion == 'price':
            token_str1 = token_str.split("~")[0]
            product_id = int(token_str.split("~")[1])
            token = self.search([('token','=',token_str1),('active','=',True),('date_start','<=',datetime.now()),('date_end','>=',datetime.now()),('product_ids','in',[product_id])])
            if token:
                self.env['pos.token.use'].create({
                        'user_id':self.env.user.id,
                        'accion':accion,
                        'use_date':datetime.now(),
                        'token_id':token.id,
                    })
                return True
            else:
                return False
        elif token:
            if token[accion] or token['permitir_todo']:
                self.env['pos.token.use'].create({
                    'user_id':self.env.user.id,
                    'accion':accion,
                    'use_date':datetime.now(),
                    'token_id':token.id,
                })
                return True
            else:
                return False
        else:
            return False
    @api.model
    def _cron_deactivate_expired_tokens(self):
        now = fields.Datetime.now()
        expired_tokens = self.search([('date_end', '<', now), ('active', '=', True)])
        expired_tokens.write({'active': False})


    @api.depends('token')
    def _compute_display_name(self):
        for line in self:
            line.display_name = line.token


    
    permitir_todo = fields.Boolean(string="Permitir todas las acciones")
    entrada_salida = fields.Boolean(string="Permitir entrada y salida de dinero")
    ordenes = fields.Boolean(string="Permitir abrir ordenes")
    pricelist = fields.Boolean(string="Permitir Lista de precios")
    discount = fields.Boolean(string="Permitir hacer descuentos")
    refund = fields.Boolean(string="Permitir hacer reembolsos")
    cerrar_caja = fields.Boolean(string="Permitir cerrar caja")
    users_use_ids = fields.One2many(
        string='Usuarios',
        comodel_name='pos.token.use',
        inverse_name='token_id',
    )
    

    
    state = fields.Selection(
        string='Estado',
        selection=[('draft', 'Borrador'), ('confirmed', 'Confirmado')]
    )
    
    def create(self, vals):
        vals.update({'state':'confirmed'})
        res = super().create(vals)
        return res

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
        'token',
        'date_start',
        'date_end',
        'active',
        'permitir_todo',
        'entrada_salida',
        ]


    @api.model
    def _load_pos_data_domain(self, data):
        return [('active', '=', True)]

    def _load_tokens_with_domain(self, domain, config_id):
        fields = self._load_pos_data_fields(config_id)
        return self.search_read(
            domain,
            fields,
            load=False)

    def _load_pos_data(self, data):
        # Add custom fields for 'formula' taxes.
        fields = set(self._load_pos_data_fields(data['pos.config']['data'][0]['id']))
        
        config = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
        domain = self._load_pos_data_domain(data)
        tokens = self._load_tokens_with_domain(domain, config.id)

        
        return {
            'data': tokens,
            'fields': fields,
        }

class PosTokenUse(models.Model):
    _name = 'pos.token.use'


    user_id = fields.Many2one(
        string='Usuario',
        comodel_name='res.users',readonly=True
    )
    accion = fields.Char(string="Accion usada",readonly=True)
    use_date = fields.Datetime(string="Fecha de uso",readonly=True)

    token_id = fields.Many2one(
        string='Token',
        comodel_name='pos.token',
    )
    
    