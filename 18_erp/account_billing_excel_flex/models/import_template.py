from odoo import fields, models


CANONICAL_TARGETS = [
    ("invoice_key", "Clave factura"),
    ("move_type", "Tipo (out_invoice, out_refund, in_invoice, in_refund)"),
    ("partner_vat", "RUC cliente/proveedor"),
    ("partner_name", "Nombre cliente/proveedor"),
    ("invoice_date", "Fecha factura"),
    ("invoice_date_due", "Fecha vencimiento"),
    ("ref", "Referencia"),
    ("currency", "Moneda (codigo)"),
    ("journal", "Diario (codigo o nombre)"),
    ("activity_code", "Codigo actividad"),
    ("activity_name", "Nombre actividad"),
    ("line_description", "Linea: descripcion"),
    ("line_quantity", "Linea: cantidad"),
    ("line_price_unit", "Linea: precio unitario"),
    ("line_discount", "Linea: descuento"),
    ("line_product", "Linea: producto (codigo o nombre)"),
    ("line_account", "Linea: cuenta contable (codigo o nombre)"),
    ("line_taxes", "Linea: impuestos (codigos separados por coma)"),
]


class AccountInvoiceImportTemplate(models.Model):
    _name = "account.invoice.import.template"
    _description = "Plantilla de Importacion de Facturas"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sheet_name = fields.Char(help="Si se deja vacio, se usa la primera hoja.")
    header_row = fields.Integer(default=1, required=True)
    line_ids = fields.One2many(
        "account.invoice.import.template.line",
        "template_id",
        string="Mapeo de columnas",
        copy=True,
    )


class AccountInvoiceImportTemplateLine(models.Model):
    _name = "account.invoice.import.template.line"
    _description = "Linea de mapeo Excel -> Odoo"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    template_id = fields.Many2one("account.invoice.import.template", required=True, ondelete="cascade")
    excel_column = fields.Char(
        required=True,
        help="Nombre exacto de columna en el Excel, respetando espacios.",
    )
    target = fields.Selection(selection=CANONICAL_TARGETS, required=True)
