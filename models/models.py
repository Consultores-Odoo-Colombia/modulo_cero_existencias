# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.product_id', 'invoice_line_ids.product_id.virtual_available')
    def _compute_stock_warning_banner(self):
        for move in self:
            move.stock_warning_banner = False
            # Check Config
            if not move.company_id.restrict_zero_invoice:
                continue

            if move.move_type in ['out_invoice', 'out_refund']:
                for line in move.invoice_line_ids:
                    if line.display_type == 'product' or (not line.display_type and line.product_id):
                        # Config check: only warn if restricted
                         if line.product_id.type != 'service':
                            stock_field = 'virtual_available' if move.company_id.stock_restriction_type == 'forecast' else 'qty_available'
                            stock_qty = getattr(line.product_id, stock_field)
                            
                            if line.quantity > stock_qty:
                                move.stock_warning_banner = _('<div class="alert alert-danger" role="alert">⚠️ <b>Alerta de Stock:</b> La cantidad solicitada supera el stock disponible (%s).</div>') % stock_qty
                                break

    def action_post(self):
        # Strict Validation on Post (Invoice Confirmation)
        _logger.info(">>>>>>>>> VALIDAR FACTURA (action_post) <<<<<<<<<<")
        for move in self:
            if not move.company_id.restrict_zero_invoice:
                continue

            if move.move_type in ['out_invoice', 'out_refund']:
                for line in move.invoice_line_ids:
                    # Validate product lines
                    if line.display_type == 'product' or (not line.display_type and line.product_id):
                        # Basic quantity/price set checks
                        if line.quantity <= 0:
                            raise ValidationError(_("No se puede confirmar: La cantidad en la línea del producto %s es 0 o negativa.") % line.product_id.name)
                        if line.price_unit <= 0:
                            raise ValidationError(_("No se puede confirmar: El precio del producto %s es 0 o negativo.") % line.product_id.name)
                        
                        # Stock Check
                        if line.product_id.type != 'service':
                             stock_field = 'virtual_available' if move.company_id.stock_restriction_type == 'forecast' else 'qty_available'
                             stock_qty = getattr(line.product_id, stock_field)
                             
                             if line.quantity > stock_qty:
                                raise ValidationError(_("Restricción Activa: No hay suficiente stock para el producto %s. (Solicitado: %s, Disponible: %s)") % (line.product_id.name, line.quantity, stock_qty))
        
        return super(AccountMove, self).action_post()





class SaleOrder(models.Model):
    _inherit = 'sale.order'

    stock_warning_banner = fields.Html(compute='_compute_stock_warning_banner')

    @api.depends('order_line.product_uom_qty', 'order_line.product_id', 'order_line.product_id.virtual_available')
    def _compute_stock_warning_banner(self):
        for order in self:
            order.stock_warning_banner = False
            if not order.company_id.restrict_zero_sale:
                continue

            for line in order.order_line:
                if line.product_id.type != 'service':
                    stock_field = 'virtual_available' if order.company_id.stock_restriction_type == 'forecast' else 'qty_available'
                    stock_qty = getattr(line.product_id, stock_field)
                    
                    if line.product_uom_qty > stock_qty:
                        order.stock_warning_banner = _('<div class="alert alert-danger" role="alert">⚠️ <b>Alerta de Stock (Ventas):</b> Cantidad supera el stock disponible (%s).</div>') % stock_qty
                        break

    def action_confirm(self):
        _logger.info(">>>>>>>>> VALIDAR VENTA (action_confirm) - INICIO <<<<<<<<<<")
        for order in self:
            if not order.company_id.restrict_zero_sale:
                _logger.info("StockRestriction: Skipping validation (Setting Disabled)")
                continue

            if not order.order_line:
                raise ValidationError(_("No se puede confirmar una orden de venta vacía."))

            for line in order.order_line:
                if line.product_uom_qty <= 0:
                     raise ValidationError(_("No se puede confirmar la venta: La cantidad del producto %s es 0 o negativa.") % line.product_id.name)
                if line.price_unit <= 0:
                     raise ValidationError(_("No se puede confirmar la venta: El precio del producto %s es 0 o negativo.") % line.product_id.name)

                if line.product_id.type != 'service':
                    stock_field = 'virtual_available' if order.company_id.stock_restriction_type == 'forecast' else 'qty_available'
                    stock_qty = getattr(line.product_id, stock_field)
                    
                    if line.product_uom_qty > stock_qty:
                         raise ValidationError(_("Restricción Activa: No hay suficiente stock para el producto %s. (Solicitado: %s, Disponible: %s)") % (line.product_id.name, line.product_uom_qty, stock_qty))
        
        return super(SaleOrder, self).action_confirm()



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    qty_on_hand_check = fields.Float(compute='_compute_qty_on_hand_check', store=False)

    @api.depends('product_id')
    def _compute_qty_on_hand_check(self):
        for line in self:
            if line.product_id:
                line.qty_on_hand_check = line.product_id.virtual_available
            else:
                line.qty_on_hand_check = 0.0

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_check_stock(self):
        for line in self:
            if not line.product_id or line.product_id.type == 'service':
                continue
            
            # Check Config - Use company_id directly if possible or env user company as fallback context
            company = line.company_id or line.order_id.company_id or self.env.company
            if not company.restrict_zero_sale:
                return

            stock_field = 'virtual_available' if company.stock_restriction_type == 'forecast' else 'qty_available'
            stock_on_hand = getattr(line.product_id, stock_field)
            
            if stock_on_hand <= 0:
                 # Clear line
                 line.product_id = False
                 line.product_uom_qty = 0
                 return {
                    'warning': {
                        'title': _("Producto no disponible (Restricción Activa)"),
                        'message': _("El producto ha sido eliminado porque no tiene stock disponible (%s) y la restricción está activada.") % stock_on_hand
                    }
                }
            
            if line.product_uom_qty > stock_on_hand:
                 ordered_qty = line.product_uom_qty
                 line.product_id = False
                 line.product_uom_qty = 0
                 return {
                    'warning': {
                        'title': _("Stock Insuficiente (Restricción Activa)"),
                        'message': _("No puedes solicitar más del stock disponible. (Solicitado: %s, Disponible: %s).") % (ordered_qty, stock_on_hand)
                    }
                }

    @api.constrains('product_uom_qty', 'price_unit', 'product_id')
    def _check_strict_values_and_stock(self):
         # Validations delegated to action_confirm
         pass

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qty_on_hand_check = fields.Float(compute='_compute_qty_on_hand_check', store=False)

    @api.depends('product_id')
    def _compute_qty_on_hand_check(self):
        for line in self:
            if line.product_id:
                line.qty_on_hand_check = line.product_id.virtual_available
            else:
                line.qty_on_hand_check = 0.0

    @api.onchange('product_id', 'quantity')
    def _onchange_product_id_check_stock(self):
        for line in self:
            if not line.product_id or line.product_id.type == 'service':
                continue
            
            if line.move_id.move_type not in ('out_invoice', 'out_refund'):
                continue
            
            # Check Config
            company = line.company_id or line.move_id.company_id or self.env.company
            if not company.restrict_zero_invoice:
                return

            stock_field = 'virtual_available' if company.stock_restriction_type == 'forecast' else 'qty_available'
            stock_on_hand = getattr(line.product_id, stock_field)
            
            if stock_on_hand <= 0:
                 line.product_id = False
                 line.quantity = 0
                 return {
                    'warning': {
                        'title': _("Producto no disponible (Restricción Activa)"),
                        'message': _("El producto ha sido eliminado porque no tiene stock disponible (%s).") % stock_on_hand
                    }
                }

            if line.quantity > stock_on_hand:
                 ordered_qty = line.quantity
                 line.product_id = False
                 line.quantity = 0
                 return {
                    'warning': {
                        'title': _("Stock Insuficiente (Restricción Activa)"),
                        'message': _("No puedes facturar más del stock disponible. (Solicitado: %s, Disponible: %s).") % (ordered_qty, stock_on_hand)
                    }
                }

    @api.constrains('quantity', 'price_unit', 'product_id')
    def _check_strict_values_and_stock_invoice(self):
         pass


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_get_warehouse_quant(self, pos_config_id):
        self.ensure_one()
        # Solo excluir servicios. Restringir 'product' (almacenable) y 'consu' (consumible/bienes)
        if self.type == 'service':
            return 999999

        pos_config = self.env['pos.config'].browse(pos_config_id)
        # Usar la ubicación de origen del tipo de operación (ubicación de stock POS)
        location = pos_config.picking_type_id.default_location_src_id
        
        if not location:
            return 0

        # Check Config
        stock_type = pos_config.company_id.stock_restriction_type
        
        if stock_type == 'forecast':
             # Use virtual_available context location logic if possible, 
             # but virtual_available is strictly Computed based on global or context.
             # For POS, if we want "Forecasted" at that location?  product.with_context(location=...).virtual_available
             
             return self.with_context(location=location.id).virtual_available
        else:
            # ON HAND (Fisico) - Using Quants
            quants = self.env['stock.quant'].search([
                ('product_id', '=', self.id),
                ('location_id', 'child_of', location.id),
            ])
            return sum(quants.mapped('available_quantity'))


