# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    restrict_zero_sale = fields.Boolean("Restringir Ventas en Cero", default=True)
    restrict_zero_invoice = fields.Boolean("Restringir Facturación en Cero", default=True)
    restrict_zero_pos = fields.Boolean("Restringir POS en Cero", default=True)
    stock_restriction_type = fields.Selection([
        ('forecast', 'Stock Pronosticado (Virtual)'),
        ('on_hand', 'Stock Disponible (Físico/A Mano)')
    ], string="Tipo de Restricción", default='forecast')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_zero_sale = fields.Boolean(
        related='company_id.restrict_zero_sale', 
        readonly=False,
        string="Restringir Ventas con Stock Cero/Negativo"
    )
    restrict_zero_invoice = fields.Boolean(
        related='company_id.restrict_zero_invoice', 
        readonly=False,
        string="Restringir Facturas con Stock Cero/Negativo"
    )
    restrict_zero_pos = fields.Boolean(
        related='company_id.restrict_zero_pos', 
        readonly=False,
        string="Restringir POS con Stock Cero/Negativo"
    )
    stock_restriction_type = fields.Selection(
        related='company_id.stock_restriction_type',
        readonly=False,
        string="Tipo de Restricción de Stock"
    )
