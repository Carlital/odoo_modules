# -*- coding: utf-8 -*-
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, timedelta

EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def _is_unknown(val):
    try:
        if not isinstance(val, str):
            return False
        s = val.strip().lower()
        return s in ('nnnn', 'se desconoce el dato')
    except Exception:
        return False

def _valid_phone(val):
    if not val:
        return True
    if not val.isdigit():
        return False
    if len(val) == 10 and val.startswith("0"):
        return True
    if len(val) == 9 and not val.startswith("0"):
        return True
    return False

def _validar_cedula_ec(cedula, aceptar_exterior=False):
    if not cedula or not cedula.isdigit() or len(cedula) != 10:
        return False
    prov = int(cedula[:2])
    if not ((1 <= prov <= 24) or (aceptar_exterior and prov == 30)):
        return False
    tercer = int(cedula[2])
    if not (0 <= tercer <= 5):
        return False
    coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    s = 0
    for i in range(9):
        prod = int(cedula[i]) * coef[i]
        if prod >= 10:
            prod -= 9
        s += prod
    dv = (10 - (s % 10)) % 10
    return dv == int(cedula[9])

def _validar_ruc_ec(ruc):
    """Valida RUC ecuatoriano para naturales (0-5), público (6) y privado (9)."""
    if not ruc or not ruc.isdigit() or len(ruc) != 13:
        return False
    tercer = int(ruc[2])
    if 0 <= tercer <= 5:
        return _validar_cedula_ec(ruc[:10])
    if tercer == 6:
        coefs = [3, 2, 7, 6, 5, 4, 3, 2]
        s = sum(int(ruc[i]) * coefs[i] for i in range(8))
        dv = 11 - (s % 11)
        if dv == 11:
            dv = 0
        elif dv == 10:
            dv = 1
        return dv == int(ruc[8])
    if tercer == 9:
        coefs = [4, 3, 2, 7, 6, 5, 4, 3, 2]
        s = sum(int(ruc[i]) * coefs[i] for i in range(9))
        dv = 11 - (s % 11)
        if dv == 11:
            dv = 0
        elif dv == 10:
            dv = 1
        return dv == int(ruc[9])
    return False

# Método de Luhn para validación de tarjetas de crédito/débito
def _validar_luhn(numero):
    if not numero:
        return False
    numero = numero.replace(" ", "")
    if not numero.isdigit():
        return False

    suma = 0
    alternar = False
    for digito in reversed(numero):
        d = int(digito)
        if alternar:
            d *= 2
            if d > 9:
                d -= 9
        suma += d
        alternar = not alternar
    return suma % 10 == 0

class CrmLead(models.Model):
    _inherit = "crm.lead"

    custom_campaign_id = fields.Many2one("crm.custom.campaign", string="Campaña (CRM Custom)", default=lambda self: self._default_campaign())
    asesor = fields.Many2one("hr.employee", string="Asesor", default=lambda self: self._default_asesor())
    fecha_negociacion = fields.Date()
    apellido_titular = fields.Char()
    nombre_titular = fields.Char()
    tipo_documento = fields.Selection([
        ("cedula", "Cedula"),
        ("pasaporte", "Pasaporte"),
        ("ruc", "RUC"),
    ])
    numero_documento = fields.Char()
    correo = fields.Char()
    cesion_contrato = fields.Boolean()
    nombres_cediente = fields.Char()
    cedula_cediente = fields.Char()
    telf_ref_1 = fields.Char()
    telf_ref_2 = fields.Char()
    nombre_referencia = fields.Char()
    parentezco = fields.Char()

    # Campos TAB Dirección titular
    provincia_domicilio = fields.Many2one("res.country.state", domain="[('country_id.code','=','EC')]")
    ciudad_domicilio = fields.Many2one("res.city", domain="[('state_id','=',provincia_domicilio)]")
    parroquia = fields.Many2one("res.parish", domain="[('city_id','=',ciudad_domicilio)]")
    sector = fields.Char(string="Sector") # Nuevo 
    misma_direccion_entrega = fields.Boolean(string="Misma dirección de entrega", default=True) # Nuevo 
    provincia_desconocida = fields.Boolean(string="Provincia desconocida", default=False)
    ciudad_desconocida = fields.Boolean(string="Ciudad desconocida", default=False)
    parroquia_desconocida = fields.Boolean(string="Parroquia desconocida", default=False)
    sector_desconocido = fields.Boolean(string="Sector desconocido", default=False) 
    # Campo para seleccionar courier (4 opciones)
    courier = fields.Selection([
        ('servientrega_despacho', 'Servientrega (Despacho)'),
        ('servientrega_oficina', 'Servientrega (Oficina)'),
        ('laarcourier', 'Laarcourier'),
        ('motorizado', 'Motorizado'),
    ], string="Courier")
    # Campo para tipo de chip (2 opciones)
    chip = fields.Selection([
        ('sim_fisico', 'SIM Físico'),
        ('sim_virtual', 'SIM Virtual'),
    ], string="Chip")
    despacho = fields.Boolean(string="Despacho", default=True) # Campo exclusivo para SIM Virtual
    # Campo para Motorizado (Many2one con creación rápida)
    motorizado_id = fields.Many2one(
        'hr.employee', 
        string="Motorizado", 
        domain="[('es_motorizado', '=', True)]",
        context={
            'default_es_motorizado_manual': True,
            'form_view_ref': 'crm_custom_lead.view_hr_employee_motorizado_form_simple'
        }
    )
    # Campos de entrega para motorizado y dirección diferente a la del titular
    calle_principal = fields.Char(string="Calle Principal")
    calle_secundaria = fields.Char(string="Calle Secundaria")
    nomenclatura = fields.Char(string="Nomenclatura")
    referencias_entrega = fields.Char(string="Referencias")
    url_google_maps = fields.Char(string="URL Google Maps")

    # Campos TAB Entrega Chip (se muestra solo con misma_direccion_entrega = False)
    provincia_entrega = fields.Many2one("res.country.state", string="Provincia de Entrega", domain="[('country_id.code','=','EC')]")
    ciudad_entrega = fields.Many2one("res.city", string="Ciudad de Entrega", domain="[('state_id','=',provincia_entrega)]")
    sector_entrega = fields.Char(string="Sector de Entrega")

    # Campos TAB pago
    forma_pago = fields.Selection([
        ('ventanilla', 'Ventanilla'),
        ('debito_bancario', 'Débito Bancario'),
        ('debito_tarjeta', 'Débito Tarjeta'),
    ], string="Forma de Pago")
    entidad_financiera = fields.Selection([
        ('banco', 'Banco'),
        ('cooperativa', 'Cooperativa'),
    ], string="Entidad Financiera")
    nombre_banco = fields.Char(string="Nombre del Banco")
    numeracion_banco = fields.Char(string="Numeración Bancaria")
    nombre_cooperativa = fields.Char(string="Nombre de la Cooperativa")
    numeracion_cooperativa = fields.Char(string="Numeración Cooperativa")
    numero_tarjeta = fields.Char(string="Número de Tarjeta")
    tipo_tarjeta = fields.Selection([
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('american_express', 'American Express'),
        ('diners_club', 'Diners Club'),
        ('discover', 'Discover'),
        ('jcb', 'JCB'),
        ('unionpay', 'UnionPay'),
        ('otros', 'Otros'),
    ], string="Tipo de Tarjeta")
    fecha_caducidad = fields.Date(string="Fecha de Caducidad")

    direccion_domicilio = fields.Char()
    descuento_oferta_comercial = fields.Char()
    bono_llamadas_ilimitadas = fields.Boolean()
    id_grabacion_contrato = fields.Char()
    carga_base = fields.Char()
    observacion = fields.Text()
    estado_asesor = fields.Char(string="Estado Asesor")
    provincia_desconocida_note = fields.Char(string=" ", compute="_compute_unknown_notes", readonly=True)
    ciudad_desconocida_note = fields.Char(string=" ", compute="_compute_unknown_notes", readonly=True)
    parroquia_desconocida_note = fields.Char(string=" ", compute="_compute_unknown_notes", readonly=True)
    sector_desconocido_note = fields.Char(string=" ", compute="_compute_unknown_notes", readonly=True)
    is_asesor_in_validacion = fields.Boolean(
        compute="_compute_is_asesor_in_validacion",
        compute_sudo=True,
        string="Asesor en Validación",
        store=False,
    )

    @api.model
    def _default_campaign(self):
        rec = self.env["crm.custom.campaign"].sudo().search([("name", "=", "Tradicional")], limit=1)
        return rec.id if rec else False

    @api.model
    def _default_asesor(self):
        emp = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)], limit=1)
        if not emp:
            emp = self.env["hr.employee"].sudo().create({
                'name': self.env.user.name or 'Empleado',
                'user_id': self.env.user.id,
                'company_id': self.env.user.company_id.id if self.env.user.company_id else False,
            })
        return emp.id

    def _stage_validacion_ref(self):
        try:
            return self.env.ref("crm_custom_lead.crm_stage_validacion")
        except Exception:
            return self.env["crm.stage"].search([("name", "=", "Validacion")], limit=1)

    def _stage_registro_ref(self):
        try:
            return self.env.ref("crm_custom_lead.crm_stage_registro")
        except Exception:
            return self.env["crm.stage"].search([("name", "=", "Registro")], limit=1)

    @api.depends('stage_id')
    def _compute_is_asesor_in_validacion(self):
        user_is_asesor = self.env.user.has_group('crm_custom_lead.group_asesor')
        stage_validacion = self._stage_validacion_ref()
        stage_validacion_id = stage_validacion.id if stage_validacion else False
        for rec in self:
            rec.is_asesor_in_validacion = bool(
                user_is_asesor and stage_validacion_id and rec.stage_id.id == stage_validacion_id
            )
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'name' in fields_list and not res.get('name'):
            emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
            domain = [('active', '=', True), ('stage_id.is_won', '=', False)]
            if emp:
                domain = [('asesor', '=', emp.id)] + domain
            count = self.env['crm.lead'].sudo().search_count(domain)
            res['name'] = 'Oportunidad %s' % (count + 1)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitize_unknown_location_vals_dict(vals)
            name = (vals.get('name') or '').strip()
            if not name or re.match(r'^Oportunidad\s+\d+$', name):
                emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
                domain = [('active', '=', True), ('stage_id.is_won', '=', False)]
                if emp:
                    domain = [('asesor', '=', emp.id)] + domain
                count = self.env['crm.lead'].sudo().search_count(domain)
                vals['name'] = 'Oportunidad %s' % (count + 1)
            if not vals.get('user_id'):
                vals['user_id'] = self.env.user.id
            if not vals.get('fecha_negociacion'):
                vals['fecha_negociacion'] = fields.Date.context_today(self)
            if not vals.get('asesor'):
                emp = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
                if not emp:
                    emp = self.env['hr.employee'].sudo().create({
                        'name': self.env.user.name or 'Empleado',
                        'user_id': self.env.user.id,
                        'company_id': self.env.user.company_id.id if self.env.user.company_id else False,
                    })
                vals['asesor'] = emp.id
            stage_registro = self._stage_registro_ref()
            if stage_registro:
                vals['stage_id'] = stage_registro.id
        records = super().create(vals_list)
        records.with_context(skip_normalization=True)._apply_normalizations()
        records._auto_stage_transition()
        return records

    @api.onchange('provincia_domicilio')
    def _onchange_provincia_domicilio(self):
        self.ciudad_domicilio = False
        self.parroquia = False
        return {'domain': {'ciudad_domicilio': [('state_id', '=', self.provincia_domicilio.id)]}}

    @api.onchange('ciudad_domicilio')
    def _onchange_ciudad_domicilio(self):
        self.parroquia = False
        return {'domain': {'parroquia': [('city_id', '=', self.ciudad_domicilio.id)]}}

    @api.onchange('provincia_desconocida')
    def _onchange_provincia_desconocida(self):
        if self.provincia_desconocida:
            self.provincia_domicilio = False

    @api.onchange('ciudad_desconocida')
    def _onchange_ciudad_desconocida(self):
        if self.ciudad_desconocida:
            self.ciudad_domicilio = False

    @api.onchange('parroquia_desconocida')
    def _onchange_parroquia_desconocida(self):
        if self.parroquia_desconocida:
            self.parroquia = False

    @api.onchange('sector_desconocido')
    def _onchange_sector_desconocido(self):
        if self.sector_desconocido:
            self.sector = False

    # Lógica reactiva misma_direccion_entrega
    @api.onchange('misma_direccion_entrega')
    def _onchange_misma_direccion_entrega(self):
        if not self.misma_direccion_entrega:
            self.courier = False
            self.chip = False
            self.despacho = True
            self.motorizado_id = False
            self.calle_principal = False
            self.calle_secundaria = False
            self.nomenclatura = False
            self.referencias_entrega = False
            self.url_google_maps = False
            self.provincia_entrega = False
            self.ciudad_entrega = False
            self.sector_entrega = False
    
    # Lógica reactiva para selección de courier
    @api.onchange('courier')
    def _onchange_courier(self):
        if self.courier == 'motorizado':
            self.chip = False
            self.despacho = False
        else:
            self.motorizado_id = False
    
    # Lógica reactiva para selección de chip
    @api.onchange('chip')
    def _onchange_chip(self):
        if self.chip != 'sim_virtual':
            self.despacho = False
    
    # Lógica reactiva para provincia_entrega
    @api.onchange('provincia_entrega')
    def _onchange_provincia_entrega(self):
        self.ciudad_entrega = False
        return {'domain': {'ciudad_entrega': [('state_id', '=', self.provincia_entrega.id)]}}

    # Lógica reactiva para forma_pago
    @api.onchange('forma_pago')
    def _onchange_forma_pago(self):
        """Resetea campos según la forma de pago seleccionada"""
        if self.forma_pago == 'ventanilla':
            self.entidad_financiera = False
            self.nombre_banco = False
            self.numeracion_banco = False
            self.nombre_cooperativa = False
            self.numeracion_cooperativa = False
            self.numero_tarjeta = False
            self.fecha_caducidad = False
        elif self.forma_pago == 'debito_bancario':
            self.numero_tarjeta = False
            self.fecha_caducidad = False
        elif self.forma_pago == 'debito_tarjeta':
            self.entidad_financiera = False
            self.nombre_banco = False
            self.numeracion_banco = False
            self.nombre_cooperativa = False
            self.numeracion_cooperativa = False

    # Validación del tipo de tarjeta
    def _get_tipo_tarjeta(self, numero):
        if not numero:
            return False
        numero = numero.replace(" ", "")
        if numero.startswith(('4',)):
            return 'visa'
        elif numero.startswith(('51', '52', '53', '54', '55')) or \
            (2221 <= int(numero[:4]) <= 2720):
            return 'mastercard'
        elif numero.startswith(('34', '37')):
            return 'amex'
        elif numero.startswith(('6011', '65')) or (644 <= int(numero[:3]) <= 649):
            return 'discover'
        elif numero.startswith(('300', '301', '302', '303', '304', '305', '36', '38', '39')):
            return 'diners'
        elif numero.startswith(('62',)):
            return 'unionpay'
        elif numero.startswith(('35',)):
            return 'jcb'
        return 'otros'

    # Valida el número de tarjeta al guardar
    @api.constrains('numero_tarjeta')
    def _constrain_numero_tarjeta_luhn(self):
        for rec in self:
            if not rec.numero_tarjeta:
                continue

            numero = rec.numero_tarjeta.replace(" ", "")
            
            # Validar longitud
            if len(numero) < 13:
                continue  # Permitir guardar incompleto
                
            if not numero.isdigit():
                raise ValidationError(_('El número de tarjeta solo puede contener dígitos'))
                
            if len(numero) > 19:
                raise ValidationError(_('El número de tarjeta debe tener máximo 19 dígitos'))
                
            if not _validar_luhn(numero):
                raise ValidationError(_('El número de tarjeta es inválido (verificación Luhn)'))

    # Valida la fecha de caducidad al guardar
    @api.constrains('fecha_caducidad')
    def _constrain_fecha_caducidad(self):
        for rec in self:
            if not rec.fecha_caducidad:
                continue
            # Calculo de la diferencia con el dia actual
            today = fields.Date.context_today(self)
            diff = (rec.fecha_caducidad - today).days
            # Debe tener al menos 10 dias (cambiar dependiendo de la política)
            if diff < 10:
                if diff < 0:
                    raise ValidationError(_('La fecha de caducidad no puede ser una fecha pasada'))
                else:
                    raise ValidationError(_('La fecha de caducidad debe ser al menos 10 días en el futuro'))

    @api.depends('provincia_desconocida', 'ciudad_desconocida', 'parroquia_desconocida', 'sector_desconocido')
    def _compute_unknown_notes(self):
        label = _('Se desconoce el dato')
        for rec in self:
            rec.provincia_desconocida_note = label if rec.provincia_desconocida else False
            rec.ciudad_desconocida_note = label if rec.ciudad_desconocida else False
            rec.parroquia_desconocida_note = label if rec.parroquia_desconocida else False
            rec.sector_desconocido_note = label if rec.sector_desconocido else False

    def write(self, vals):
        if vals:
            self._sanitize_unknown_location_vals_dict(vals)
        # Asesor no puede editar ni mover en etapa Validacion
        if self.env.user.has_group('crm_custom_lead.group_asesor'):
            stage_validacion = self._stage_validacion_ref()
            if stage_validacion:
                allow_stage_transition = bool(self.env.context.get('allow_stage_transition'))
                for rec in self:
                    target_stage_id = vals.get('stage_id', rec.stage_id.id)
                    in_valid = rec.stage_id.id == stage_validacion.id
                    to_valid = ('stage_id' in vals and target_stage_id == stage_validacion.id)
                    if (in_valid or to_valid) and not allow_stage_transition:
                        raise AccessError(_('No puede editar ni mover oportunidades en etapa Validación.'))
        if self.env.context.get('skip_normalization'):
            return super().write(vals)
        res = super().write(vals)
        self.with_context(skip_normalization=True)._apply_normalizations()
        self._auto_stage_transition()
        return res

    def _apply_normalizations(self):
        for rec in self:
            update_vals = {}
            if rec.numero_documento:
                cleaned = rec.numero_documento.strip()
                if cleaned != rec.numero_documento:
                    update_vals['numero_documento'] = cleaned
            if rec.cedula_cediente:
                cleaned = rec.cedula_cediente.strip()
                if cleaned != rec.cedula_cediente:
                    update_vals['cedula_cediente'] = cleaned
            if rec.correo:
                cleaned = rec.correo.strip().lower()
                if cleaned != rec.correo:
                    update_vals['correo'] = cleaned
            if update_vals:
                super(CrmLead, rec.with_context(skip_normalization=True)).write(update_vals)

    def _run_custom_normalizations(self):
        self._apply_normalizations()

    def _is_prevalidation_complete(self):
        self.ensure_one()
        return all([
            bool(self.apellido_titular and self.apellido_titular.strip()),
            bool(self.nombre_titular and self.nombre_titular.strip()),
            bool(self.numero_documento and self.numero_documento.strip()),
            bool(self.correo and self.correo.strip()),
            bool(self.direccion_domicilio and self.direccion_domicilio.strip()),
            self.tipo_documento,
            (self.provincia_desconocida or bool(self.provincia_domicilio)),
            (self.ciudad_desconocida or bool(self.ciudad_domicilio)),
            (self.parroquia_desconocida or bool(self.parroquia)),
        ])

    def _auto_stage_transition(self):
        stage_validacion = self._stage_validacion_ref()
        stage_registro = self._stage_registro_ref()
        for rec in self:
            if stage_validacion and rec.stage_id.id == stage_validacion.id:
                # Paso a etapa de Validación
                rec._run_custom_validations()
                continue
            go_validacion = False
            if rec._is_prevalidation_complete():
                try:
                    rec._run_custom_validations()
                    go_validacion = True
                except ValidationError:
                    go_validacion = False
            if go_validacion and stage_validacion:
                rec._convert_unknowns_on_validacion()
                rec.with_context(allow_stage_transition=True).write({'stage_id': stage_validacion.id})
            elif stage_registro and rec.stage_id.id != stage_registro.id:
                rec.write({'stage_id': stage_registro.id})

    def _convert_unknowns_on_validacion(self):
        label = _('Se desconoce el dato')
        char_fields = [
            'apellido_titular','nombre_titular','numero_documento','correo',
            'direccion_domicilio','nombres_cediente','cedula_cediente',
            'telf_ref_1','telf_ref_2','nombre_referencia','parentezco','forma_pago',
            'entidad_bancaria','tipo_cuenta','numero_cuenta_tarjeta','descuento_oferta_comercial',
            'id_grabacion_contrato','carga_base','observacion'
        ]
        updates = {}
        for fname in char_fields:
            val = getattr(self, fname, False)
            if _is_unknown(val):
                updates[fname] = label
        if updates:
            super(CrmLead, self.with_context(skip_normalization=True)).write(updates)

    def _sanitize_unknown_location_vals_dict(self, vals):
        if vals.get('provincia_desconocida'):
            vals['provincia_domicilio'] = False
        if vals.get('ciudad_desconocida'):
            vals['ciudad_domicilio'] = False
        if vals.get('parroquia_desconocida'):
            vals['parroquia'] = False
        if vals.get('sector_desconocido'):
            vals['sector'] = False

    @api.constrains('provincia_desconocida','ciudad_desconocida','parroquia_desconocida','sector_desconocido',
                    'provincia_domicilio','ciudad_domicilio','parroquia','sector')
    def _constrain_unknown_location_consistency(self):
        for rec in self:
            if rec.provincia_desconocida and rec.provincia_domicilio:
                raise ValidationError(_('Si Provincia es desconocida no puede seleccionar una provincia.'))
            if rec.ciudad_desconocida and rec.ciudad_domicilio:
                raise ValidationError(_('Si Ciudad es desconocida no puede seleccionar una ciudad.'))
            if rec.parroquia_desconocida and rec.parroquia:
                raise ValidationError(_('Si Parroquia es desconocida no puede seleccionar una parroquia.'))
            if rec.sector_desconocido and rec.sector:
                raise ValidationError(_('Si Sector es desconocido no puede ingresar un sector.'))

    def _check_document(self, tipo, numero):
        if not tipo or not numero or _is_unknown(numero):
            return
        if tipo == 'cedula':
            if not _validar_cedula_ec(numero):
                raise ValidationError(_('Cédula ecuatoriana inválida.'))
        elif tipo == 'ruc':
            if not _validar_ruc_ec(numero):
                raise ValidationError(_('RUC ecuatoriano inválido.'))
        elif tipo == 'pasaporte':
            if len(numero) < 6:
                raise ValidationError(_('Pasaporte debe tener al menos 6 caracteres.'))

    def _check_email(self, email):
        if _is_unknown(email):
            return
        if email and not EMAIL_REGEX.match(email):
            raise ValidationError(_('Correo no es valido.'))

    def _check_cedula_simple(self, val, label):
        if _is_unknown(val):
            return
        if val and not (val.isdigit() and len(val) == 10):
            raise ValidationError(_('%s debe tener 10 digitos.') % label)

    def _check_phone(self, val, label):
        if _is_unknown(val):
            return
        if val and not _valid_phone(val):
            raise ValidationError(_('%s invalido. Use 9 digitos (sin 0) o 10 digitos empezando por 0.') % label)

    def _run_custom_validations(self):
        for rec in self:
            rec._check_document(rec.tipo_documento, rec.numero_documento)
            if rec.tipo_documento == 'cedula' and rec.numero_documento and not _is_unknown(rec.numero_documento):
                pass
            rec._check_cedula_simple(rec.cedula_cediente, _('Cedula cediente'))
            rec._check_email(rec.correo)
            # rec._check_phone(rec.numero_a_portar, _('Numero a portar'))
            rec._check_phone(rec.telf_ref_1, _('Telefono referencia 1'))
            rec._check_phone(rec.telf_ref_2, _('Telefono referencia 2'))

    @api.constrains('tipo_documento', 'numero_documento', 'cedula_cediente', 'correo', 'telf_ref_1', 'telf_ref_2')
    def _constrains_custom_fields(self):
        self._run_custom_validations()

    @api.constrains('stage_id', 'apellido_titular','nombre_titular','tipo_documento','numero_documento',
                    'correo','provincia_domicilio','ciudad_domicilio','parroquia',
                    'provincia_desconocida','ciudad_desconocida','parroquia_desconocida','direccion_domicilio')
    def _constrain_prevalidacion_before_stage(self):
        stage_validacion = self._stage_validacion_ref()
        for rec in self:
            if stage_validacion and rec.stage_id.id == stage_validacion.id:
                if not all([
                    bool(rec.apellido_titular and rec.apellido_titular.strip()),
                    bool(rec.nombre_titular and rec.nombre_titular.strip()),
                    bool(rec.numero_documento and rec.numero_documento.strip()),
                    bool(rec.correo and rec.correo.strip()),
                    bool(rec.direccion_domicilio and rec.direccion_domicilio.strip()),
                    rec.tipo_documento,
                    (rec.provincia_desconocida or bool(rec.provincia_domicilio)),
                    (rec.ciudad_desconocida or bool(rec.ciudad_domicilio)),
                    (rec.parroquia_desconocida or bool(rec.parroquia)),
                ]):
                    raise ValidationError(_('Complete todos los campos obligatorios antes de Validación.'))
                rec._run_custom_validations()