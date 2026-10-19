# Facturacion Flexible con Excel (Odoo 18)

Este modulo permite:

- Importar facturas desde archivos Excel (`.xlsx`) con mapeo configurable por plantilla.
- Adaptar distintos nombres de columnas sin desarrollar codigo adicional.
- Asociar facturas a actividades de facturacion vinculadas a usuarios.
- Filtrar la visualizacion de facturas por actividad seleccionada (incluye selector tipo radio).
- Generar reporte PDF de facturas por actividad y rango de fechas.

## Requisitos

- Odoo 18
- Modulos base: `account`, `contacts`
- Dependencia Python: `openpyxl`

## Formato de importacion Excel

Puedes usar una o varias hojas. En cada plantilla defines:

- Hoja (`sheet_name`) opcional
- Fila de encabezado (`header_row`)
- Mapeo `Columna Excel -> Campo canonico`

Campos canonicos soportados:

- `invoice_key`
- `move_type`
- `partner_vat`
- `partner_name`
- `invoice_date`
- `invoice_date_due`
- `ref`
- `currency`
- `journal`
- `activity_code`
- `activity_name`
- `line_description`
- `line_quantity`
- `line_price_unit`
- `line_discount`
- `line_product`
- `line_account`
- `line_taxes`

### Nota sobre agrupacion

- Si mapeas `invoice_key`, filas con la misma clave se agrupan en una sola factura con varias lineas.
- Si no mapeas `invoice_key`, cada fila genera una factura individual.

## Flujo recomendado

1. Crear actividades de facturacion.
2. Asignar actividades a usuarios.
3. Crear plantilla de importacion y definir mapeo de columnas.
4. Importar Excel desde el wizard.
5. Elegir actividad visible para cada usuario.
6. Generar reporte por actividad y fechas.

## Menus principales

- Facturacion Flexible / Configuracion / Actividades
- Facturacion Flexible / Configuracion / Plantillas Excel
- Facturacion Flexible / Importar Facturas
- Facturacion Flexible / Elegir Actividad
- Facturacion Flexible / Reporte por Actividad
