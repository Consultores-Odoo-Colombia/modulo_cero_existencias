# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.product_id', 'invoice_line_ids.product_id.free_qty')
    def _compute_stock_warning_banner(self):
        for move in self:
            move.stock_warning_banner = False
            if move.move_type in ['out_invoice', 'out_refund']:
                for line in move.invoice_line_ids:
                    if line.display_type == 'product' or (not line.display_type and line.product_id):
                         if line.product_id.type == 'product' and line.quantity > line.product_id.free_qty:
                            move.stock_warning_banner = _('<div class="alert alert-danger" role="alert">⚠️ <b>Alerta de Stock:</b> Uno o más productos superan la cantidad libre disponible. No podrá confirmar esta factura.</div>')
                            break

    def action_post(self):
        # Strict Validation on Post (Invoice Confirmation) - Safety Net
        _logger.info(">>>>>>>>> VALIDAR FACTURA (action_post) <<<<<<<<<<")
        for move in self:
            if move.move_type in ['out_invoice', 'out_refund']:
                for line in move.invoice_line_ids:
                    # Validate product lines
                    if line.display_type == 'product' or (not line.display_type and line.product_id):
                        if line.quantity <= 0:
                            raise ValidationError(_("No se puede confirmar: La cantidad en la línea del producto %s es 0 o negativa.") % line.product_id.name)
                        if line.price_unit <= 0:
                            raise ValidationError(_("No se puede confirmar: El precio del producto %s es 0 o negativo.") % line.product_id.name)
                        
                        # Stock Check
                        if line.product_id.type == 'product':
                             if line.quantity > line.product_id.free_qty:
                                raise ValidationError(_("No hay suficientes existencias libres para el producto %s. (Solicitado: %s, Libre: %s)") % (line.product_id.name, line.quantity, line.product_id.free_qty))
        
        return super(AccountMove, self).action_post()


class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('lines.qty', 'lines.product_id', 'lines.product_id.free_qty')
    def _compute_stock_warning_banner(self):
        for order in self:
            order.stock_warning_banner = False
            for line in order.lines:
                if line.product_id.type == 'product' and line.qty > line.product_id.free_qty:
                    order.stock_warning_banner = _('<div class="alert alert-danger" role="alert">⚠️ <b>Alerta de Stock:</b> Tienes productos con cantidad superior al stock libre.</div>')
                    break


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('order_line.product_uom_qty', 'order_line.product_id', 'order_line.product_id.free_qty')
    def _compute_stock_warning_banner(self):
        for order in self:
            order.stock_warning_banner = False
            for line in order.order_line:
                if line.product_id.type == 'product' and line.product_uom_qty > line.product_id.free_qty:
                    order.stock_warning_banner = _('<div class="alert alert-danger" role="alert">⚠️ <b>Alerta de Stock:</b> Tienes productos con cantidad superior al stock libre. No podrás confirmar la venta.</div>')
                    break

    def action_confirm(self):
        _logger.info(">>>>>>>>> VALIDAR VENTA (action_confirm) - INICIO <<<<<<<<<<")
        # Safety Net for Confirmation
        for order in self:
            if not order.order_line:
                raise ValidationError(_("No se puede confirmar una orden de venta vacía. Agregue líneas de producto."))

            for line in order.order_line:
                if line.product_uom_qty <= 0:
                     raise ValidationError(_("No se puede confirmar la venta: La cantidad del producto %s es 0 o negativa.") % line.product_id.name)
                if line.price_unit <= 0:
                     raise ValidationError(_("No se puede confirmar la venta: El precio del producto %s es 0 o negativo.") % line.product_id.name)

                if line.product_id.type == 'product':
                    if line.product_uom_qty > line.product_id.free_qty:
                         raise ValidationError(_("No hay suficientes existencias libres para el producto %s. (Solicitado: %s, Libre: %s)") % (line.product_id.name, line.product_uom_qty, line.product_id.free_qty))
        
        _logger.info(">>>>>>>>> VALIDAR VENTA (action_confirm) - FIN EXITOSO <<<<<<<<<<")
        return super(SaleOrder, self).action_confirm()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_uom_qty', 'price_unit', 'product_id')
    def _check_strict_values_and_stock(self):
        # Triggered on Save/Create of the line (Draft state)
        for line in self:
            if line.product_id.type == 'product':
                # 1. Price and Quantity strictly positive
                if line.product_uom_qty <= 0:
                    raise ValidationError(_("La cantidad del producto %s debe ser mayor a 0.") % line.product_id.name)
                if line.price_unit <= 0:
                    raise ValidationError(_("El precio del producto %s debe ser mayor a 0.") % line.product_id.name)
                
                # 2. Strict Stock Check (Free Qty)
                # We interpret "Stock a la mano" in the context of availability as "Free Qty" (Hand - Reserved)
                if line.product_uom_qty > line.product_id.free_qty:
                    raise ValidationError(_("Stock insuficiente para %s. Solicitado: %s, Disponible(Libre): %s") % (line.product_id.name, line.product_uom_qty, line.product_id.free_qty))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.constrains('quantity', 'price_unit', 'product_id')
    def _check_strict_values_and_stock_invoice(self):
        # Triggered on Save/Create of the line (Draft state)
        for line in self:
            # Only apply to Customer Invoices/Refunds validation logic, but constrains run on all moves.
            # We filter by move_type usually, but line.move_id might not be fully set in some contexts? 
            # Safe checking move_type.
            if line.move_id.move_type in ['out_invoice', 'out_refund']:
                if line.display_type == 'product' or (not line.display_type and line.product_id):
                     if line.quantity <= 0:
                        raise ValidationError(_("La cantidad en la factura para %s debe ser mayor a 0.") % line.product_id.name)
                     if line.price_unit <= 0:
                        raise ValidationError(_("El precio en la factura para %s debe ser mayor a 0.") % line.product_id.name)
                     
                     # Stock Check
                     if line.product_id.type == 'product':
                        if line.quantity > line.product_id.free_qty:
                             raise ValidationError(_("Stock insuficiente para %s. Solicitado: %s, Disponible(Libre): %s") % (line.product_id.name, line.quantity, line.product_id.free_qty))


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.constrains('qty', 'product_id', 'price_unit')
    def _check_stock_availability_pos(self):
        for line in self:
            if line.product_id and line.product_id.type == 'product':
                # Strict Validation: Quantity checks
                if line.qty <= 0:
                    raise ValidationError(_("La cantidad en el POS no puede ser 0 o negativa para el producto %s.") % line.product_id.name)

                if line.price_unit <= 0:
                    raise ValidationError(_("El precio del producto %s no puede ser 0 o negativo.") % line.product_id.name)

                # Stock Check (Use free_qty)
                if line.qty > line.product_id.free_qty:
                    raise ValidationError(_("No hay suficientes existencias libres para el producto %s en el POS. (Solicitado: %s, Libre: %s)") % (line.product_id.name, line.qty, line.product_id.free_qty))
