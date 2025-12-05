from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import Command

class TestZeroRestrictions(TransactionCase):

    def setUp(self):
        super(TestZeroRestrictions, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 10.0,
            'taxes_id': False,
        })
        self.product_zero = self.env['product.product'].create({
            'name': 'Test Product Zero',
            'list_price': 0.0,
            'taxes_id': False,
        })
        # Intentar obtener una config existente para evitar problemas de dependencias/campos faltantes en entorno de desarrollo
        self.pos_config = self.env['pos.config'].search([], limit=1)
        if not self.pos_config:
            # Fallback si no hay ninguna (raro en dev con demo data, clave para CI limpio)
            self.pos_config = self.env['pos.config'].create({'name': 'Main Test'})

    def test_zero_invoice_restriction(self):
        """Test que impide confirmar una factura de cliente en 0"""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_zero.id,
                    'price_unit': 0.0,
                    'quantity': 1,
                })
            ]
        })
        
        # Debe lanzar ValidationError al postear con monto 0
        with self.assertRaises(ValidationError):
            invoice.action_post()

    def test_valid_invoice(self):
        """Test que permite confirmar una factura válida"""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product.id,
                    'price_unit': 10.0,
                    'quantity': 1,
                })
            ]
        })
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_zero_pos_order_restriction(self):
        """Test que impide crear un pedido POS con monto 0"""
        # Intentar crear un pedido con monto 0
        with self.assertRaises(ValidationError):
            self.env['pos.order'].create({
                'session_id': self.pos_config.current_session_id.id or self.env['pos.session'].create({'config_id': self.pos_config.id}).id,
                'amount_total': 0.0,
                'amount_tax': 0.0,
                'amount_paid': 0.0,
                'amount_return': 0.0,
                'lines': [
                    Command.create({
                        'product_id': self.product_zero.id,
                        'qty': 1,
                        'price_unit': 0.0,
                        'price_subtotal': 0.0,
                        'price_subtotal_incl': 0.0,
                    })
                ]
            })

    def test_valid_pos_order(self):
        """Test que permite un pedido POS válido"""
        # Asegurarse de tener una sesión abierta o crearla
        session = self.pos_config.current_session_id
        if not session:
             session = self.env['pos.session'].create({'config_id': self.pos_config.id})
             
        order = self.env['pos.order'].create({
            'session_id': session.id,
            'amount_total': 10.0,
            'amount_tax': 0.0,
            'amount_paid': 10.0,
            'amount_return': 0.0,
            'lines': [
                Command.create({
                    'product_id': self.product.id,
                    'qty': 1,
                    'price_unit': 10.0,
                    'price_subtotal': 10.0,
                    'price_subtotal_incl': 10.0,
                })
            ]
        })
        self.assertTrue(order.id, "El pedido debería crearse correctamente")
