# -*- coding: utf-8 -*-
{
    'name': 'ACS Sale Order Line Stock',
    'summary': """
        Añade columnas de Stock Actual y Stock Virtual en las líneas de
        pedidos de venta, basado en el almacén seleccionado.
    """,
    'description': """
        Este módulo mejora la experiencia del usuario en ventas al mostrar
        directamente en las líneas del pedido de venta (sale.order.line)
        dos campos cruciales:
        - Stock Actual (Quantity On Hand)
        - Stock Virtual (Forecasted Quantity)

        Los valores se calculan dinámicamente según el producto y el almacén
        seleccionado en la cabecera del pedido de venta. Si el almacén cambia,
        las cantidades de stock se recalculan automáticamente.
    """,
    'author': "Juan Ayala, ACSistemas Peru",
    'website': "https://www.acsistemasperu.com",
    'category': 'Sales/Sales',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',

    # Dependencias necesarias para que el módulo funcione
    'depends': [
        'sale_management',
        'stock',
    ],

    # Archivos de datos que siempre se cargan
    'data': [
        'views/sale_order_view.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
}
