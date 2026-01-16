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

    # Dependencias necesarias para heredar de account, point_of_sale y sale
    'depends': ['base', 'account', 'point_of_sale', 'sale', 'sale_management', 'sale_stock'],

    'assets': {
        'web.assets_backend': [
             'modulo_cero_existencias/static/src/js/stock_restricted_list_renderer.js',
             'modulo_cero_existencias/static/src/xml/stock_restricted_list_renderer.xml',
             'modulo_cero_existencias/static/src/js/stock_restricted_section_and_note_field.js',
        ],
        'point_of_sale._assets_pos': [
            'modulo_cero_existencias/static/src/js/pos_stock_restriction.js',
        ],
    },

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_views.xml',
        'views/sale_views.xml',
    ],

    'installable': True,
    'application': False,
}

