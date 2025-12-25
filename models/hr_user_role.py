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
    color = fields.Integer(string="Color Index", default=0)
    user_count = fields.Integer(
        string="Number of Users",
        compute="_compute_user_count"
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Role name must be unique!')
    ]

    @api.depends('groups_id')
    def _compute_user_count(self):
        """Count users who have this role's groups"""
        for role in self:
            if role.groups_id:
                # Count users who have at least one group from this role
                users = self.env['res.users'].search([
                    ('groups_id', 'in', role.groups_id.ids)
                ])
                role.user_count = len(users)
            else:
                role.user_count = 0

    def action_view_users(self):
        """View users with this role"""
        self.ensure_one()
        return {
            'name': f'Users with {self.name} Role',
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('groups_id', 'in', self.groups_id.ids)],
            'context': {'create': False}
        }