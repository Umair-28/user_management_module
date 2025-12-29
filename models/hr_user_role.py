from odoo import models, fields

class HrUserRole(models.Model):
    _name = "hr.user.role"
    _description = "HR User Role"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
