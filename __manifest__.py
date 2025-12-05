# -*- coding: utf-8 -*-
{
    'name': "Restricción de Ventas en Cero",

    'summary': "Impide confirmar facturas y pedidos POS con monto cero.",

    'description': """
        Este módulo añade una validación estricta para evitar que se procesen
        facturas de cliente (account.move) y pedidos de punto de venta (pos.order)
        con un monto total de 0.
    """,

    'author': "consultoresodoocolombia",
    'website': "https://consultoresodoocolombia.odoo.com/",

    'category': 'Accounting',
    'version': '18.0.1.0.0',
    'license': 'OPL-1',

    # Dependencias necesarias para heredar de account y point_of_sale
    'depends': ['base', 'account', 'point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': False,
}

