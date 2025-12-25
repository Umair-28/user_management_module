# -*- coding: utf-8 -*-
# from odoo import http


# class HrUserManagement(http.Controller):
#     @http.route('/hr_user_management/hr_user_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_user_management/hr_user_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_user_management.listing', {
#             'root': '/hr_user_management/hr_user_management',
#             'objects': http.request.env['hr_user_management.hr_user_management'].search([]),
#         })

#     @http.route('/hr_user_management/hr_user_management/objects/<model("hr_user_management.hr_user_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_user_management.object', {
#             'object': obj
#         })

