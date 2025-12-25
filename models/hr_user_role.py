from odoo import models, fields, api

class HrUserRole(models.Model):
    _name = "hr.user.role"
    _description = "User Role"
    _order = "sequence, name"

    name = fields.Char(string="Role Name", required=True)
    sequence = fields.Integer(default=10)
    description = fields.Text(string="Description")
    groups_id = fields.Many2many(
        "res.groups",
        relation="hr_user_role_groups_rel",
        column1="role_id",
        column2="group_id",
        string="Access Rights"
    )
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color Index")

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Role name must be unique!')
    ]