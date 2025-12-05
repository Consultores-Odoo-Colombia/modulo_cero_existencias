# -*- coding: utf-8 -*-
# from odoo import http


# class ModuloCeroExistencias(http.Controller):
#     @http.route('/modulo_cero_existencias/modulo_cero_existencias', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/modulo_cero_existencias/modulo_cero_existencias/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('modulo_cero_existencias.listing', {
#             'root': '/modulo_cero_existencias/modulo_cero_existencias',
#             'objects': http.request.env['modulo_cero_existencias.modulo_cero_existencias'].search([]),
#         })

#     @http.route('/modulo_cero_existencias/modulo_cero_existencias/objects/<model("modulo_cero_existencias.modulo_cero_existencias"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('modulo_cero_existencias.object', {
#             'object': obj
#         })

