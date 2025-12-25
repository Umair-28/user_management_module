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
    user_role = fields.Selection([
        ('hr', 'HR Manager'),
        ('accountant', 'Accountant'),
        ('sales', 'Sales Manager'),
        ('purchase', 'Purchase Manager'),
        ('warehouse', 'Warehouse Manager'),
        ('inventory', 'Inventory User'),
    ], string="User Role", required=True, help="Select the role for this user")
    
    groups_id = fields.Many2many(
        "res.groups",
        string="Access Rights",
        help="Groups will be automatically assigned based on selected role"
    )

    @api.onchange('user_role')
    def _onchange_user_role(self):
        """Automatically populate groups based on selected role"""
        if self.user_role:
            groups = self._get_groups_for_role(self.user_role)
            self.groups_id = [(6, 0, groups)]

    def _get_groups_for_role(self, role):
        """Return group IDs based on role"""
        group_ids = []
        
        # Base user group (required for all users)
        base_user = self.env.ref('base.group_user', raise_if_not_found=False)
        if base_user:
            group_ids.append(base_user.id)
        
        if role == 'hr':
            # HR Groups
            hr_groups = self.env['res.groups'].search([
                '|',
                ('name', 'in', ['Officer', 'HR Officer', 'Manager']),
                '&',
                ('category_id.name', '=', 'Human Resources'),
                ('name', '!=', 'Administrator')
            ])
            group_ids.extend(hr_groups.ids)
            
        elif role == 'accountant':
            # Accounting Groups
            accounting_groups = self.env['res.groups'].search([
                '|',
                ('name', 'in', ['Billing', 'Adviser', 'Accountant']),
                '&',
                ('category_id.name', '=', 'Accounting'),
                ('name', '!=', 'Adviser')
            ])
            group_ids.extend(accounting_groups.ids)
            
            # Add Invoicing group
            invoicing = self.env.ref('account.group_account_invoice', raise_if_not_found=False)
            if invoicing:
                group_ids.append(invoicing.id)
                
        elif role == 'sales':
            # Sales Groups
            sales_groups = self.env['res.groups'].search([
                '|',
                ('name', 'in', ['User: Own Documents Only', 'User: All Documents', 'Administrator']),
                '&',
                ('category_id.name', '=', 'Sales'),
                ('name', '!=', 'Administrator')
            ])
            group_ids.extend(sales_groups.ids)
            
            # Add CRM User group
            crm_user = self.env.ref('crm.group_use_lead', raise_if_not_found=False)
            if crm_user:
                group_ids.append(crm_user.id)
                
        elif role == 'purchase':
            # Purchase Groups
            purchase_groups = self.env['res.groups'].search([
                '|',
                ('name', 'in', ['User', 'Purchase User']),
                '&',
                ('category_id.name', '=', 'Purchase'),
                ('name', '!=', 'Manager')
            ])
            group_ids.extend(purchase_groups.ids)
            
        elif role == 'warehouse':
            # Warehouse/Inventory Groups
            warehouse_groups = self.env['res.groups'].search([
                '|',
                ('name', 'in', ['User', 'Warehouse User']),
                '&',
                ('category_id.name', '=', 'Inventory'),
                ('name', '!=', 'Administrator')
            ])
            group_ids.extend(warehouse_groups.ids)
            
        elif role == 'inventory':
            # Inventory User
            inventory_user = self.env.ref('stock.group_stock_user', raise_if_not_found=False)
            if inventory_user:
                group_ids.append(inventory_user.id)
        
        return list(set(group_ids))  # Remove duplicates

    @api.model
    def default_get(self, fields_list):
        res = super(HrCreateUserWizard, self).default_get(fields_list)
        
        # Get employee_id from context
        if self._context.get('active_model') == 'hr.employee' and self._context.get('active_id'):
            res['employee_id'] = self._context.get('active_id')
            
            # Check if employee already has a user_role set
            employee = self.env['hr.employee'].browse(self._context.get('active_id'))
            if hasattr(employee, 'x_user_role') and employee.x_user_role:
                res['user_role'] = employee.x_user_role
        
        return res

    def action_create_user(self):
        self.ensure_one()

        if self.password != self.confirm_password:
            raise UserError("Passwords do not match.")

        if not self.login:
            raise UserError("Login is required.")
            
        if not self.user_role:
            raise UserError("User Role is required.")

        # Check if user with this login already exists
        existing_user = self.env['res.users'].sudo().search([('login', '=', self.login)], limit=1)
        if existing_user:
            raise UserError(f"A user with login '{self.login}' already exists.")

        # Prepare user values
        user_vals = {
            "name": self.employee_id.name,
            "login": self.login,
            "email": self.login,
            "password": self.password,
        }

        # Create user with password
        user = self.env["res.users"].sudo().create(user_vals)

        # Get groups for the selected role
        group_ids = self._get_groups_for_role(self.user_role)
        
        # Set groups
        if group_ids:
            user.sudo().write({
                "groups_id": [(6, 0, group_ids)]
            })

        # Link employee to user
        self.employee_id.sudo().write({
            "user_id": user.id
        })
        
        # Update employee's role field if it exists
        if hasattr(self.employee_id, 'x_user_role'):
            self.employee_id.sudo().write({
                "x_user_role": self.user_role
            })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Success",
                "message": f"User created successfully for {self.employee_id.name}",
                "type": "success",
                "sticky": False,
            }
        }
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
