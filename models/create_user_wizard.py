from odoo import models, fields, api
from odoo.exceptions import UserError

class HrCreateUserWizard(models.TransientModel):
    _name = "hr.create.user.wizard"
    _description = "Create User With Password"

    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        readonly=True
    )
    login = fields.Char(required=True)
    password = fields.Char(required=True)
    confirm_password = fields.Char(required=True)
    role_id = fields.Many2one(
        "hr.user.role",
        string="Role",
        help="Select a predefined role for this user"
    )
    groups_id = fields.Many2many(
        "res.groups",
        string="Access Rights",
        help="Select the access rights/groups for this user"
    )

    @api.model
    def default_get(self, fields_list):
        res = super(HrCreateUserWizard, self).default_get(fields_list)
        
        # Add default Employee group
        employee_group = self.env.ref('base.group_user', raise_if_not_found=False)
        if employee_group and 'groups_id' in fields_list:
            res['groups_id'] = [(6, 0, [employee_group.id])]
        
        return res

    @api.onchange('role_id')
    def _onchange_role_id(self):
        """Update groups when role is selected"""
        if self.role_id:
            # Get base employee group
            employee_group = self.env.ref('base.group_user', raise_if_not_found=False)
            group_ids = [employee_group.id] if employee_group else []
            
            # Add role's groups
            group_ids.extend(self.role_id.groups_id.ids)
            
            self.groups_id = [(6, 0, group_ids)]

    def action_create_user(self):
        self.ensure_one()

        if self.password != self.confirm_password:
            raise UserError("Passwords do not match.")

        if not self.login:
            raise UserError("Login is required.")

        # Prepare user values
        user_vals = {
            "name": self.employee_id.name,
            "login": self.login,
            "email": self.login,
            "password": self.password,
        }

        # Create user with password
        user = self.env["res.users"].sudo().create(user_vals)

        # Set groups separately after user creation
        if self.groups_id:
            user.sudo().write({
                "groups_id": [(6, 0, self.groups_id.ids)]
            })

        # Link employee to user
        self.employee_id.sudo().write({
            "user_id": user.id
        })

        return {"type": "ir.actions.act_window_close"}
# from odoo import models, fields, api
# from odoo.exceptions import UserError

# class HrCreateUserWizard(models.TransientModel):
#     _name = "hr.create.user.wizard"
#     _description = "Create User With Password"

#     employee_id = fields.Many2one(
#         "hr.employee",
#         required=True,
#         readonly=True
#     )
#     login = fields.Char(required=True)
#     password = fields.Char(required=True)
#     confirm_password = fields.Char(required=True)
#     groups_id = fields.Many2many(
#         "res.groups",
#         string="Access Rights",
#         help="Select the access rights/groups for this user"
#     )

#     @api.model
#     def default_get(self, fields_list):
#         res = super(HrCreateUserWizard, self).default_get(fields_list)
        
#         if 'groups_id' in fields_list:
#             default_groups = []
            
#             # Get base employee group (required)
#             employee_group = self.env.ref('base.group_user', raise_if_not_found=False)
#             if employee_group:
#                 default_groups.append(employee_group.id)
            
#             # Exclude patterns for admin/manager groups
#             exclude_keywords = ['admin', 'manager', 'system', 'erp_manager', 'settings']
            
#             # Find all user-level groups (basic access groups)
#             all_groups = self.env['res.groups'].search([
#                 ('name', 'ilike', 'user'),
#                 ('name', 'not ilike', 'portal'),
#                 ('name', 'not ilike', 'public'),
#             ])
            
#             for group in all_groups:
#                 # Exclude admin/manager level groups
#                 if not any(keyword in group.name.lower() for keyword in exclude_keywords):
#                     default_groups.append(group.id)
            
#             if default_groups:
#                 res['groups_id'] = [(6, 0, list(set(default_groups)))]  # Remove duplicates
        
#         return res

#     def action_create_user(self):
#         self.ensure_one()

#         if self.password != self.confirm_password:
#             raise UserError("Passwords do not match.")

#         if not self.login:
#             raise UserError("Login is required.")

#         # Prepare user values
#         user_vals = {
#             "name": self.employee_id.name,
#             "login": self.login,
#             "email": self.login,
#             "password": self.password,
#         }

#         # Create user with password
#         user = self.env["res.users"].sudo().create(user_vals)

#         # Set groups separately after user creation
#         if self.groups_id:
#             user.sudo().write({
#                 "groups_id": [(6, 0, self.groups_id.ids)]
#             })

#         # Link employee to user
#         self.employee_id.sudo().write({
#             "user_id": user.id
#         })

#         return {"type": "ir.actions.act_window_close"}
