# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('amount_total', 'state', 'move_type')
    def _check_amount_not_zero(self):
        for record in self:
            # Validar facturas de cliente, proveedor y sus rectificativas (refunds)
            if record.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund'] and record.state == 'posted':
                if record.amount_total == 0:
                    raise ValidationError(_("No se permite publicar una factura o nota de crédito con monto total 0."))

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.constrains('amount_total', 'state')
    def _check_pos_amount_not_zero(self):
        for order in self:
            # Validar pedidos en cualquier estado que no sea cancelado/borrador si se desea, 
            # pero usualmente la restricción es al validar el pedido.
            # En POS, los pedidos llegan usualmente como 'paid' o 'done' o 'invoiced'.
            # Validaremos si el monto es 0. 
            # Nota: Permitir devoluciones (monto negativo) podría ser necesario, 
            # el requerimiento dice "no deje hacer factura administrativa en 0 y pos".
            # Asumiremos que se refiere a venta (monto 0). Devoluciones suelen ser negativas.
            # Si amount_total es 0 exactamente, bloqueamos.
            if order.amount_total == 0:
                 raise ValidationError(_("No se permite crear un pedido POS con monto total 0."))

