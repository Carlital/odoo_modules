from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class BcAttribute(models.Model):
    _name = 'bc.attribute'
    _description = 'Atributo dinámico de BC'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', required=True)
    field_type = fields.Selection([('char','Texto'),('text','Texto largo'),('bool','Booleano'),('float','Número')], string='Tipo', default='char')
    required = fields.Boolean(string='Requerido', default=False)

    _sql_constraints = [
        ('bc_attribute_code_uniq', 'unique(code)', 'El código del atributo debe ser único'),
    ]

class BcPlanAttribute(models.Model):
    _name = 'bc.plan.attribute'
    _description = 'Valor de atributo por plan BC'

    plan_id = fields.Many2one('bc.plan', string='Plan', required=True, ondelete='cascade')
    attribute_id = fields.Many2one('bc.attribute', string='Atributo', required=True, ondelete='cascade')
    value_char = fields.Char(string='Valor (texto)')
    value_text = fields.Text(string='Valor (texto largo)')
    value_bool = fields.Boolean(string='Valor (S/N)')
    value_float = fields.Float(string='Valor (número)')

    _sql_constraints = [
        ('bc_plan_attr_unique', 'unique(plan_id, attribute_id)', 'Ya existe este atributo para el plan'),
    ]

    def get_display_value(self):
        self.ensure_one()
        t = self.attribute_id.field_type
        if t == 'bool':
            return 'S' if self.value_bool else 'N'
        if t == 'float':
            return str(self.value_float) if self.value_float is not None else 'S/N'
        if t == 'text':
            return self.value_text or 'S/N'
        return self.value_char or 'S/N'