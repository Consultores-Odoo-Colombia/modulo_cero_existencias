# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountMove(models.Model):
    _inherit = 'account.move'

    stock_warning_banner = fields.Html(string='Stock Warning', compute='_compute_stock_warning_banner', store=False)

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.product_id')
    def _compute_stock_warning_banner(self):
        for move in self:
            invalid_lines = move.invoice_line_ids.filtered(lambda l: l.product_id and l.quantity == 0)
            if invalid_lines and move.move_type in ['out_invoice', 'out_refund']:
                move.stock_warning_banner = """
                    <div class="alert alert-danger" role="alert" style="margin-bottom:0px;">
                        <strong>Advertencia:</strong> No se permiten agregar más productos si existen líneas con stock cero.
                    </div>
                """
            else:
                move.stock_warning_banner = False

    @api.constrains('amount_total', 'state', 'move_type')
    def _check_amount_not_zero(self):
        for record in self:
            if record.move_type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund'] and record.state == 'posted':
                if record.amount_total == 0:
                    raise ValidationError(_("No se permite publicar una factura o nota de crédito con monto total 0."))

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids_sequential_check(self):
        invalid_lines = self.invoice_line_ids.filtered(lambda l: l.product_id and l.quantity == 0)
        if invalid_lines:
             return {
                'warning': {
                    'title': _("Restricción de Stock"),
                    'message': _("No se permiten agregar más productos con stock cero. Por favor corríjala.")
                }
            }


class PosOrder(models.Model):
    _inherit = 'pos.order'

    stock_warning_banner = fields.Html(string='Stock Warning', compute='_compute_stock_warning_banner', store=False)

    @api.depends('lines.qty', 'lines.product_id')
    def _compute_stock_warning_banner(self):
        for order in self:
            invalid_lines = order.lines.filtered(lambda l: l.product_id and l.qty == 0)
            if invalid_lines:
                order.stock_warning_banner = """
                    <div class="alert alert-danger" role="alert" style="margin-bottom:0px;">
                        <strong>Advertencia:</strong> No se permiten agregar más productos si existen líneas con stock cero.
                    </div>
                """
            else:
                order.stock_warning_banner = False

    @api.constrains('amount_total', 'state')
    def _check_pos_amount_not_zero(self):
        for order in self:
            if order.amount_total == 0:
                 raise ValidationError(_("No se permite crear un pedido POS con monto total 0."))

    @api.onchange('lines')
    def _onchange_lines_sequential_check(self):
        invalid_lines = self.lines.filtered(lambda l: l.product_id and l.qty == 0)
        if invalid_lines:
             return {
                'warning': {
                    'title': _("Restricción de Stock"),
                    'message': _("No se permiten agregar más productos con stock cero. Por favor corríjala.")
                }
            }

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        # Strict stock check on confirmation
        for order in self:
            for line in order.order_line:
                if line.product_id.type == 'product':
                    # Check Quantity On Hand (qty_available) instead of Virtual
                    if line.product_uom_qty > line.product_id.qty_available:
                         raise ValidationError(_("No se puede confirmar la venta. El producto %s no tiene suficiente stock a mano (Solicitado: %s, Disponible: %s).") % (line.product_id.name, line.product_uom_qty, line.product_id.qty_available))
        return super(SaleOrder, self).action_confirm()

    stock_warning_banner = fields.Html(string='Stock Warning', compute='_compute_stock_warning_banner', store=False)

    @api.depends('order_line.product_uom_qty', 'order_line.product_id')
    def _compute_stock_warning_banner(self):
        for order in self:
            invalid_lines = order.order_line.filtered(lambda l: l.product_id and l.product_uom_qty == 0)
            if invalid_lines:
                order.stock_warning_banner = """
                    <div class="alert alert-danger" role="alert" style="margin-bottom:0px;">
                        <strong>Advertencia:</strong> No se permiten agregar más productos si existen líneas con stock cero (cantidad 0).
                        Por favor, corrija o elimine las líneas marcadas antes de continuar.
                    </div>
                """
            else:
                order.stock_warning_banner = False

    @api.onchange('order_line')
    def _onchange_order_line_sequential_check(self):
        # 1. Check for invalid lines (0 qty)
        invalid_lines = self.order_line.filtered(lambda l: l.product_id and l.product_uom_qty == 0)
        
        if invalid_lines:
            return {
                'warning': {
                    'title': _("Restricción de Stock"),
                    'message': _("No se permiten agregar más productos con stock cero. Por favor corrija los productos marcados.")
                }
            }

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_uom_qty', 'product_id')
    def _check_stock_availability(self):
        for line in self:
            if line.product_id and line.product_id.type == 'product':
                # Block if requested quantity is greater than available
                # Note: virtual_available usually does not subtract the current draft line.
                # If it did, we would need to add line.product_uom_qty back before comparing.
                # Assuming standard behavior where draft doesn't reduce virtual_available:
                if line.product_uom_qty > line.product_id.virtual_available:
                     raise ValidationError(_("No hay suficientes existencias para el producto %s. (Solicitado: %s, Disponible: %s)") % (line.product_id.name, line.product_uom_qty, line.product_id.virtual_available))

    @api.onchange('product_uom_qty', 'product_id')
    def _onchange_product_id_check_availability(self):
        if self.product_id and self.product_id.type == 'product':
            # Debug Log
            print(f"[DEBUG] _onchange_product_id: Product={self.product_id.name}, Qty={self.product_uom_qty}, Virtual={self.product_id.virtual_available}")
            if self.product_uom_qty > self.product_id.virtual_available:
                self.product_uom_qty = 0
                self.product_id = False # STRICT: Clear product to prevent line creation
                return {
                    'warning': {
                        'title': _("Advertencia de Stock"),
                        'message': _("No hay suficientes existencias para el producto %s. (Solicitado: %s, Disponible: %s) - Línea limpiada.") % (self.product_id.name, self.product_uom_qty, self.product_id.virtual_available)
                    }
                }

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    virtual_available = fields.Float(related='product_id.virtual_available', string='Forecasted Quantity', readonly=True)
    
    # Fields for qty_at_date_widget
    virtual_available_at_date = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    scheduled_date = fields.Datetime(compute='_compute_qty_at_date')
    forecast_expected_date = fields.Datetime(compute='_compute_qty_at_date')
    free_qty_today = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    qty_available_today = fields.Float(compute='_compute_qty_at_date')
    warehouse_id = fields.Many2one('stock.warehouse', compute='_compute_warehouse_id', store=False)
    qty_to_deliver = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    is_mto = fields.Boolean(compute='_compute_qty_at_date')
    # Widget expects 'state' to determine logic (draft vs sale) and 'move_ids' for popover link
    # We mock 'state' to 'draft' so it uses virtual_available logic vs free_qty logic
    state = fields.Selection([('draft', 'Draft'), ('sale', 'Sale')], default='draft', compute='_compute_qty_at_date')

    def _compute_warehouse_id(self):
        default_warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        for line in self:
            line.warehouse_id = default_warehouse

    # Mock move_ids to prevent JS crash on click (widget expects One2many)
    move_ids = fields.One2many('stock.move', compute='_compute_empty_moves')

    def _compute_empty_moves(self):
        for line in self:
            line.move_ids = False

    @api.depends('product_id', 'move_id.invoice_date', 'quantity')
    def _compute_qty_at_date(self):
        for line in self:
            line.scheduled_date = line.move_id.invoice_date or fields.Datetime.now()
            line.forecast_expected_date = False
            line.qty_to_deliver = line.quantity
            line.is_mto = False
            line.state = 'draft' 
            # Widget uses move_ids to link forecast; we provide empty list to avoid crash
            line.move_ids = False 
            if line.product_id:
                line.virtual_available_at_date = line.product_id.virtual_available
                line.free_qty_today = line.product_id.free_qty
                line.qty_available_today = line.product_id.qty_available
            else:
                line.virtual_available_at_date = 0
                line.free_qty_today = 0
                line.qty_available_today = 0

    @api.constrains('quantity', 'product_id')
    def _check_stock_availability_invoice(self):
        for line in self:
            # Only check for customer invoices
            if line.move_id.move_type == 'out_invoice' and line.product_id and line.product_id.type == 'product':
                if line.quantity > line.product_id.virtual_available:
                    raise ValidationError(_("No hay suficientes existencias para el producto %s en la factura. (Solicitado: %s, Disponible: %s)") % (line.product_id.name, line.quantity, line.product_id.virtual_available))

    @api.onchange('quantity', 'product_id')
    def _onchange_quantity_check_availability(self):
        # Check only for customer invoices
        if self.move_id.move_type == 'out_invoice' and self.product_id and self.product_id.type == 'product':
            if self.quantity > self.product_id.virtual_available:
                self.quantity = 0
                self.product_id = False # STRICT: Clear product to prevent line creation
                return {
                    'warning': {
                        'title': _("Advertencia de Stock"),
                        'message': _("No hay suficientes existencias para el producto %s. (Solicitado: %s, Disponible: %s) - Línea limpiada.") % (self.product_id.name, self.quantity, self.product_id.virtual_available)
                    }
                }

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    virtual_available = fields.Float(related='product_id.virtual_available', string='Forecasted Quantity', readonly=True)

    # Fields for qty_at_date_widget
    virtual_available_at_date = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    scheduled_date = fields.Datetime(compute='_compute_qty_at_date')
    forecast_expected_date = fields.Datetime(compute='_compute_qty_at_date')
    free_qty_today = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    qty_available_today = fields.Float(compute='_compute_qty_at_date')
    warehouse_id = fields.Many2one('stock.warehouse', compute='_compute_warehouse_id', store=False)
    qty_to_deliver = fields.Float(compute='_compute_qty_at_date', digits='Product Unit of Measure')
    is_mto = fields.Boolean(compute='_compute_qty_at_date')
    state = fields.Selection([('draft', 'Draft'), ('sale', 'Sale')], default='draft', compute='_compute_qty_at_date')

    def _compute_warehouse_id(self):
        for line in self:
            if line.order_id.session_id.config_id.warehouse_id:
                line.warehouse_id = line.order_id.session_id.config_id.warehouse_id
            else:
                line.warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

    # Mock move_ids
    move_ids = fields.One2many('stock.move', compute='_compute_empty_moves')

    def _compute_empty_moves(self):
        for line in self:
            line.move_ids = False

    @api.depends('product_id', 'order_id.date_order', 'qty')
    def _compute_qty_at_date(self):
        for line in self:
            line.scheduled_date = line.order_id.date_order or fields.Datetime.now()
            line.forecast_expected_date = False
            line.qty_to_deliver = line.qty
            line.is_mto = False
            line.state = 'draft'
            line.move_ids = False
            if line.product_id:
                line.virtual_available_at_date = line.product_id.virtual_available
                line.free_qty_today = line.product_id.free_qty
                line.qty_available_today = line.product_id.qty_available
            else:
                line.virtual_available_at_date = 0
                line.free_qty_today = 0
                line.qty_available_today = 0

    @api.constrains('qty', 'product_id')
    def _check_stock_availability_pos(self):
        for line in self:
            if line.product_id and line.product_id.type == 'product':
                if line.qty > line.product_id.virtual_available:
                    raise ValidationError(_("No hay suficientes existencias para el producto %s en el POS. (Solicitado: %s, Disponible: %s)") % (line.product_id.name, line.qty, line.product_id.virtual_available))

    @api.onchange('qty', 'product_id')
    def _onchange_qty_check_availability(self):
        if self.product_id and self.product_id.type == 'product':
            if self.qty > self.product_id.virtual_available:
                self.qty = 0
                self.product_id = False # STRICT: Clear product to prevent line creation
                return {
                    'warning': {
                        'title': _("Advertencia de Stock"),
                        'message': _("No hay suficientes existencias para el producto %s. (Solicitado: %s, Disponible: %s) - Línea limpiada.") % (self.product_id.name, self.qty, self.product_id.virtual_available)
                    }
                }
