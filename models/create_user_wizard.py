from odoo import models, fields, api
from odoo.exceptions import UserError


class HrCreateUserWizard(models.TransientModel):
    _name = "hr.create.user.wizard"
    _description = "Create/Update User With Password"

    employee_id = fields.Many2one("hr.employee", required=True, readonly=True)
    existing_user_id = fields.Many2one("res.users", string="Existing User", readonly=True)
    is_update_mode = fields.Boolean(compute="_compute_is_update_mode", store=False)
    
    login = fields.Char(string="Login/Email",required=True)
    password = fields.Char(string="Password")
    confirm_password = fields.Char(string="Confirm Password")
    user_role_ids = fields.Many2many("hr.user.role", string="User Roles", required=True)

    groups_id = fields.Many2many(
        "res.groups",
        string="Access Rights",
        help="Groups will be automatically assigned based on selected role",
    )

    @api.depends('employee_id', 'employee_id.user_id')
    def _compute_is_update_mode(self):
        """Check if we're updating an existing user or creating new"""
        for wizard in self:
            wizard.is_update_mode = bool(wizard.employee_id.user_id)

    @api.onchange('user_role_ids')
    def _onchange_user_roles(self):
        """Auto-populate groups based on selected roles"""
        group_ids = []
        for role in self.user_role_ids:
            group_ids.extend(self._get_groups_for_role(role.code))

        self.groups_id = [(6, 0, list(set(group_ids)))]

    @api.model
    def default_get(self, fields_list):
        """Pre-fill wizard with existing user data if updating"""
        res = super(HrCreateUserWizard, self).default_get(fields_list)

        # Get employee from context
        employee_id = self._context.get("default_employee_id")
        if employee_id:
            employee = self.env["hr.employee"].browse(employee_id)
            res["employee_id"] = employee_id

            # If employee has a user, pre-fill the form (UPDATE MODE)
            if employee.user_id:
                user = employee.user_id
                res["existing_user_id"] = user.id
                res["login"] = user.login
                
                # Pre-fill roles if stored on employee
                if hasattr(employee, "x_user_role_ids") and employee.x_user_role_ids:
                    res["user_role_ids"] = [(6, 0, employee.x_user_role_ids.ids)]
                
                # Pre-fill groups
                res["groups_id"] = [(6, 0, user.groups_id.ids)]
            else:
                # CREATE MODE - use work email if available
                if employee.work_email:
                    res["login"] = employee.work_email

        return res

    def _get_groups_for_role(self, role):
        """Return group IDs based on role"""
        group_ids = []

        # Base user group (required for all users)
        base_user = self.env.ref("base.group_user", raise_if_not_found=False)
        if base_user:
            group_ids.append(base_user.id)

        if role == "hr":
            # HR Groups - Main HR Module
            hr_groups = self.env["res.groups"].search(
                [
                    "|",
                    ("name", "in", ["Officer", "HR Officer", "Manager"]),
                    "&",
                    ("category_id.name", "=", "Human Resources"),
                    ("name", "!=", "Administrator"),
                ]
            )
            group_ids.extend(hr_groups.ids)

            # Time Off / Leaves Management
            timeoff_groups = self.env["res.groups"].search(
                [
                    ("category_id.name", "=", "Time Off"),
                    ("name", "in", ["Officer", "Manager", "User"]),
                ]
            )
            group_ids.extend(timeoff_groups.ids)

            # Attendance
            attendance_groups = self.env["res.groups"].search(
                [
                    ("category_id.name", "=", "Attendances"),
                    ("name", "in", ["Officer", "Manager"]),
                ]
            )
            group_ids.extend(attendance_groups.ids)

            # Additional specific HR groups by XML ID
            hr_xmlid_groups = [
                "hr.group_hr_user",
                "hr_holidays.group_hr_holidays_user",
                "hr_attendance.group_hr_attendance",
                "hr_recruitment.group_hr_recruitment_user",
                "hr_appraisal.group_hr_appraisal_user",
                "hr_expense.group_hr_expense_user",
                "hr_contract.group_hr_contract_manager",
            ]

            for xmlid in hr_xmlid_groups:
                try:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group:
                        group_ids.append(group.id)
                except:
                    pass

        elif role == "accountant":
            # Accounting groups
            accounting_groups = self.env["res.groups"].search(
                [
                    "|",
                    ("name", "in", ["Billing", "Adviser", "Accountant"]),
                    "&",
                    ("category_id.name", "=", "Accounting"),
                    ("name", "!=", "Adviser"),
                ]
            )
            group_ids.extend(accounting_groups.ids)

            accounting_xmlid_groups = [
                "account.group_account_user",
                "account.group_account_readonly",
                "account.group_account_invoice",
                "account_accountant.group_account_accountant",
            ]

            for xmlid in accounting_xmlid_groups:
                try:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group:
                        group_ids.append(group.id)
                except:
                    pass

        elif role == "sales":
            # Sales groups
            sales_groups = self.env["res.groups"].search(
                [
                    ("category_id.name", "=", "Sales"),
                    ("name", "in", ["User: Own Documents Only", "User: All Documents", "User"]),
                ]
            )
            group_ids.extend(sales_groups.ids)

            sales_xmlid_groups = [
                "sales_team.group_sale_salesman",
                "sale.group_sale_user",
                "crm.group_use_lead",
            ]

            for xmlid in sales_xmlid_groups:
                try:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group:
                        group_ids.append(group.id)
                except:
                    pass

        elif role == "purchase":
            purchase_xmlid_groups = ["purchase.group_purchase_user"]
            for xmlid in purchase_xmlid_groups:
                try:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group:
                        group_ids.append(group.id)
                except:
                    pass

        elif role == "warehouse":
            warehouse_xmlid_groups = [
                "stock.group_stock_user",
                "stock.group_stock_multi_locations",
            ]
            for xmlid in warehouse_xmlid_groups:
                try:
                    group = self.env.ref(xmlid, raise_if_not_found=False)
                    if group:
                        group_ids.append(group.id)
                except:
                    pass

        elif role == "inventory":
            inventory_user = self.env.ref("stock.group_stock_user", raise_if_not_found=False)
            if inventory_user:
                group_ids.append(inventory_user.id)

        return list(set(group_ids))

    def action_create_user(self):
        """Create new user or update existing user"""
        self.ensure_one()

        # If updating existing user
        if self.is_update_mode and self.existing_user_id:
            return self._update_existing_user()
        
        # Otherwise create new user
        return self._create_new_user()

    def _create_new_user(self):
        """Create a brand new user"""
        # Validations
        if not self.password or not self.confirm_password:
            raise UserError("Password and Confirm Password are required when creating a new user.")
        
        if self.password != self.confirm_password:
            raise UserError("Passwords do not match.")

        if not self.login:
            raise UserError("Login is required.")

        if not self.user_role_ids:
            raise UserError("At least one role must be selected.")

        # Check existing user
        existing_user = self.env["res.users"].sudo().search([("login", "=", self.login)], limit=1)
        if existing_user:
            raise UserError(f"A user with login '{self.login}' already exists.")

        # Create user
        user_vals = {
            "name": self.employee_id.name,
            "login": self.login,
            "email": self.login,
            "password": self.password,
        }

        user = self.env["res.users"].sudo().create(user_vals)

        # Collect groups from ALL roles
        group_ids = []
        for role in self.user_role_ids:
            group_ids.extend(self._get_groups_for_role(role.code))

        group_ids = list(set(group_ids))

        if group_ids:
            user.sudo().write({"groups_id": [(6, 0, group_ids)]})

        # Link employee to user
        self.employee_id.sudo().write({"user_id": user.id})

        # Store roles on employee (if custom field exists)
        if hasattr(self.employee_id, "x_user_role_ids"):
            self.employee_id.sudo().write({"x_user_role_ids": [(6, 0, self.user_role_ids.ids)]})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Success",
                "message": f"User created successfully for {self.employee_id.name}",
                "type": "success",
                "sticky": True,
            },
        }

    def _update_existing_user(self):
        """Update existing user's roles and groups"""
        user = self.existing_user_id

        if not self.user_role_ids:
            raise UserError("At least one role must be selected.")

        # Update login/email if changed
        if self.login != user.login:
            # Check if new login already exists
            existing = self.env["res.users"].sudo().search([
                ("login", "=", self.login),
                ("id", "!=", user.id)
            ], limit=1)
            if existing:
                raise UserError(f"A user with login '{self.login}' already exists.")
            
            user.sudo().write({
                "login": self.login,
                "email": self.login,
            })

        # Update password if provided
        if self.password:
            if self.password != self.confirm_password:
                raise UserError("Passwords do not match.")
            user.sudo().write({"password": self.password})

        # Collect groups from ALL roles
        group_ids = []
        for role in self.user_role_ids:
            group_ids.extend(self._get_groups_for_role(role.code))

        group_ids = list(set(group_ids))

        if group_ids:
            user.sudo().write({"groups_id": [(6, 0, group_ids)]})

        # Update roles on employee (if custom field exists)
        if hasattr(self.employee_id, "x_user_role_ids"):
            self.employee_id.sudo().write({"x_user_role_ids": [(6, 0, self.user_role_ids.ids)]})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Success",
                "message": f"User updated successfully for {self.employee_id.name}",
                "type": "success",
                "sticky": True,
            },
        }
# from odoo import models, fields, api
# from odoo.exceptions import UserError


# class HrCreateUserWizard(models.TransientModel):
#     _name = "hr.create.user.wizard"
#     _description = "Create User With Password"

#     employee_id = fields.Many2one("hr.employee", required=True, readonly=True)
#     login = fields.Char(required=True)
#     password = fields.Char(required=True)
#     confirm_password = fields.Char(required=True)
#     user_role_ids = fields.Many2many("hr.user.role", string="User Roles", required=True)

#     groups_id = fields.Many2many(
#         "res.groups",
#         string="Access Rights",
#         help="Groups will be automatically assigned based on selected role",
#     )

#     @api.onchange('user_role_ids')
#     def _onchange_user_roles(self):
#         group_ids = []
#         for role in self.user_role_ids:
#             group_ids.extend(self._get_groups_for_role(role.code))

#         self.groups_id = [(6, 0, list(set(group_ids)))]


#     # @api.onchange("user_role")
#     # def _onchange_user_role(self):
#     #     """Automatically populate groups based on selected role"""
#     #     if self.user_role:
#     #         groups = self._get_groups_for_role(self.user_role)
#     #         self.groups_id = [(6, 0, groups)]

#     def _get_groups_for_role(self, role):
#         """Return group IDs based on role"""
#         group_ids = []

#         # Base user group (required for all users)
#         base_user = self.env.ref("base.group_user", raise_if_not_found=False)
#         if base_user:
#             group_ids.append(base_user.id)

#         if role == "hr":
#             # HR Groups - Main HR Module
#             hr_groups = self.env["res.groups"].search(
#                 [
#                     "|",
#                     ("name", "in", ["Officer", "HR Officer", "Manager"]),
#                     "&",
#                     ("category_id.name", "=", "Human Resources"),
#                     ("name", "!=", "Administrator"),
#                 ]
#             )
#             group_ids.extend(hr_groups.ids)

#             # Time Off / Leaves Management
#             timeoff_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Time Off"),
#                     ("name", "in", ["Officer", "Manager", "User"]),
#                 ]
#             )
#             group_ids.extend(timeoff_groups.ids)

#             # Attendance
#             attendance_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Attendances"),
#                     ("name", "in", ["Officer", "Manager"]),
#                 ]
#             )
#             group_ids.extend(attendance_groups.ids)

#             # Recruitment
#             recruitment_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Recruitment"),
#                     ("name", "in", ["Officer", "User"]),
#                 ]
#             )
#             group_ids.extend(recruitment_groups.ids)

#             # Appraisal
#             appraisal_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Appraisals"),
#                     ("name", "in", ["User", "Manager", "Officer"]),
#                 ]
#             )
#             group_ids.extend(appraisal_groups.ids)

#             # Payroll (if installed)
#             payroll_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Payroll"),
#                     ("name", "in", ["User", "Officer"]),
#                 ]
#             )
#             group_ids.extend(payroll_groups.ids)

#             # Expenses
#             expense_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Expenses"),
#                     ("name", "in", ["User", "Team Approver", "Manager"]),
#                 ]
#             )
#             group_ids.extend(expense_groups.ids)

#             # Fleet Management
#             fleet_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Fleet"),
#                     ("name", "in", ["User", "Officer", "Manager"]),
#                 ]
#             )
#             group_ids.extend(fleet_groups.ids)

#             # Referral (Employee Referral)
#             referral_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Referral"),
#                 ]
#             )
#             group_ids.extend(referral_groups.ids)

#             # Contracts (HR Contracts)
#             contract_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Contracts"),
#                     ("name", "in", ["User", "Manager"]),
#                 ]
#             )
#             group_ids.extend(contract_groups.ids)

#             # Skills Management
#             skills_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Skills"),
#                 ]
#             )
#             group_ids.extend(skills_groups.ids)

#             # Planning/Schedule (if installed)
#             planning_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Planning"),
#                     ("name", "in", ["User", "Manager"]),
#                 ]
#             )
#             group_ids.extend(planning_groups.ids)

#             # Timesheet (for HR tracking employee hours)
#             timesheet_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Timesheets"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(timesheet_groups.ids)

#             # Additional specific HR groups by XML ID (more reliable)
#             hr_xmlid_groups = [
#                 "hr.group_hr_user",  # HR User
#                 "hr_holidays.group_hr_holidays_user",  # Time Off User
#                 "hr_attendance.group_hr_attendance",  # Attendance User
#                 "hr_recruitment.group_hr_recruitment_user",  # Recruitment User
#                 "hr_appraisal.group_hr_appraisal_user",  # Appraisal User
#                 "hr_expense.group_hr_expense_user",  # Expense User
#                 # 'fleet.fleet_group_user',
#                 "hr_contract.group_hr_contract_manager",  # Contract Manager
#             ]

#             for xmlid in hr_xmlid_groups:
#                 try:
#                     group = self.env.ref(xmlid, raise_if_not_found=False)
#                     if group:
#                         group_ids.append(group.id)
#                 except:
#                     pass

#         elif role == "accountant":
#             # Accounting Groups - Main Accounting Module
#             accounting_groups = self.env["res.groups"].search(
#                 [
#                     "|",
#                     ("name", "in", ["Billing", "Adviser", "Accountant"]),
#                     "&",
#                     ("category_id.name", "=", "Accounting"),
#                     ("name", "!=", "Adviser"),
#                 ]
#             )
#             group_ids.extend(accounting_groups.ids)

#             # Invoicing/Billing
#             invoicing_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Invoicing"),
#                 ]
#             )
#             group_ids.extend(invoicing_groups.ids)

#             # Payment
#             payment_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Payment"),
#                 ]
#             )
#             group_ids.extend(payment_groups.ids)

#             # Expenses (Accountant needs to approve/process expenses)
#             expense_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Expenses"),
#                     (
#                         "name",
#                         "in",
#                         ["User", "Team Approver", "All Approver", "Manager"],
#                     ),
#                 ]
#             )
#             group_ids.extend(expense_groups.ids)

#             # Assets Management (Fixed Assets)
#             asset_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Assets"),
#                 ]
#             )
#             group_ids.extend(asset_groups.ids)

#             # Budget Management
#             budget_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Budget"),
#                 ]
#             )
#             group_ids.extend(budget_groups.ids)

#             # Analytic Accounting
#             analytic_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Analytic Accounting"),
#                 ]
#             )
#             group_ids.extend(analytic_groups.ids)

#             # Documents (Financial Documents)
#             documents_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Documents"),
#                     ("name", "in", ["User", "Manager"]),
#                 ]
#             )
#             group_ids.extend(documents_groups.ids)

#             # Sign (Document Signing for financial docs)
#             sign_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Sign"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(sign_groups.ids)

#             # Studio (if accountants need to customize views)
#             # studio_groups = self.env['res.groups'].search([
#             #     ('category_id.name', '=', 'Studio'),
#             # ])
#             # group_ids.extend(studio_groups.ids)

#             # Additional accounting groups by XML ID (more reliable)
#             accounting_xmlid_groups = [
#                 "account.group_account_user",  # Accountant User
#                 "account.group_account_readonly",  # Show Accounting
#                 "account.group_account_invoice",  # Billing
#                 "account_accountant.group_account_accountant",  # Accountant (Full Access)
#                 "account.group_account_manager",  # Billing Manager
#                 "analytic.group_analytic_accounting",  # Analytic Accounting
#                 "account.group_warning_account",  # Warnings in Accounting
#                 "account_payment.group_account_payment",  # Payment
#                 "account_asset.group_account_assets",  # Assets Management
#                 "hr_expense.group_hr_expense_team_approver",  # Expense Team Approver
#                 "hr_expense.group_hr_expense_manager",  # Expense Manager
#                 "account_budget.group_account_budget",  # Budget Management
#             ]

#             for xmlid in accounting_xmlid_groups:
#                 try:
#                     group = self.env.ref(xmlid, raise_if_not_found=False)
#                     if group:
#                         group_ids.append(group.id)
#                 except:
#                     pass

#         elif role == "sales":
#             # Sales Groups - Main Sales Module
#             sales_groups = self.env["res.groups"].search(
#                 [
#                     "|",
#                     (
#                         "name",
#                         "in",
#                         ["User: Own Documents Only", "User: All Documents", "User"],
#                     ),
#                     "&",
#                     ("category_id.name", "=", "Sales"),
#                     ("name", "!=", "Administrator"),
#                 ]
#             )
#             group_ids.extend(sales_groups.ids)

#             # CRM Groups - Customer Relationship Management
#             crm_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "CRM"),
#                     (
#                         "name",
#                         "in",
#                         ["User", "User: All Documents", "User: Own Documents Only"],
#                     ),
#                 ]
#             )
#             group_ids.extend(crm_groups.ids)

#             # Point of Sale (POS)
#             pos_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Point of Sale"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(pos_groups.ids)

#             # Quotations/Sales Orders
#             quotation_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Quotations"),
#                 ]
#             )
#             group_ids.extend(quotation_groups.ids)

#             # Subscriptions (Recurring Sales)
#             subscription_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Subscriptions"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(subscription_groups.ids)

#             # eCommerce (if sales manage online store)
#             ecommerce_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "eCommerce"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(ecommerce_groups.ids)

#             # Rental (Product Rental Management)
#             rental_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Rental"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(rental_groups.ids)

#             # Marketing Automation (for sales campaigns)
#             marketing_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Marketing Automation"),
#                     ("name", "in", ["User"]),
#                 ]
#             )
#             group_ids.extend(marketing_groups.ids)

#             # Email Marketing
#             email_marketing_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Email Marketing"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(email_marketing_groups.ids)

#             # SMS Marketing
#             sms_marketing_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "SMS Marketing"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(sms_marketing_groups.ids)

#             # Social Marketing
#             social_marketing_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Social Marketing"),
#                     ("name", "in", ["User"]),
#                 ]
#             )
#             group_ids.extend(social_marketing_groups.ids)

#             # Events (Event Management for sales events)
#             event_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Events"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(event_groups.ids)

#             # Surveys (Customer surveys and feedback)
#             survey_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Surveys"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(survey_groups.ids)

#             # Appointments (Customer meeting scheduling)
#             appointment_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Appointments"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(appointment_groups.ids)

#             # Helpdesk (Customer support for sales)
#             helpdesk_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Helpdesk"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(helpdesk_groups.ids)

#             # Live Chat (Customer engagement)
#             livechat_groups = self.env["res.groups"].search(
#                 [
#                     ("category_id.name", "=", "Live Chat"),
#                     ("name", "in", ["User", "Officer"]),
#                 ]
#             )
#             group_ids.extend(livechat_groups.ids)

#             # VoIP (Phone calls with customers)
#             voip_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "VoIP"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(voip_groups.ids)

#             # Invoicing (Sales need to see invoices)
#             invoicing_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Invoicing"), ("name", "in", ["Billing"])]
#             )
#             group_ids.extend(invoicing_groups.ids)

#             # Sign (For sales contracts and quotes)
#             sign_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Sign"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(sign_groups.ids)

#             # Documents (Sales documents management)
#             documents_groups = self.env["res.groups"].search(
#                 [("category_id.name", "=", "Documents"), ("name", "in", ["User"])]
#             )
#             group_ids.extend(documents_groups.ids)

#             # Additional sales groups by XML ID (more reliable)
#             sales_xmlid_groups = [
#                 "sales_team.group_sale_salesman",  # Salesperson
#                 "sales_team.group_sale_salesman_all_leads",  # See All Leads
#                 "sales_team.group_sale_manager",  # Sales Manager (optional)
#                 "sale.group_sale_user",  # Sales User
#                 "crm.group_use_lead",  # Use Leads
#                 "crm.group_use_recurring_revenues",  # Recurring Revenues
#                 "point_of_sale.group_pos_user",  # POS User
#                 "sale_subscription.group_sale_subscription",  # Subscriptions
#                 "website_sale.group_website_restricted_editor",  # eCommerce Editor
#                 "mass_mailing.group_mass_mailing_user",  # Email Marketing User
#                 "mass_mailing_sms.group_mass_mailing_sms_user",  # SMS Marketing User
#                 "social_marketing.group_social_marketing_user",  # Social Marketing User
#                 "event.group_event_user",  # Event User
#                 "survey.group_survey_user",  # Survey User
#                 "appointment.group_appointment_user",  # Appointment User
#                 "helpdesk.group_helpdesk_user",  # Helpdesk User
#                 "im_livechat.im_livechat_group_user",  # Live Chat User
#                 "voip.group_voip_user",  # VoIP User
#                 "sale_rental.group_rental_user",  # Rental User
#                 "marketing_automation.group_marketing_automation_user",  # Marketing Automation
#                 "account.group_account_invoice",
#             ]

#             for xmlid in sales_xmlid_groups:
#                 try:
#                     group = self.env.ref(xmlid, raise_if_not_found=False)
#                     if group:
#                         group_ids.append(group.id)
#                 except:
#                     pass

#         elif role == "purchase":
#             # Purchase Groups
#             purchase_groups = self.env["res.groups"].search(
#                 [
#                     "|",
#                     ("name", "in", ["User", "Purchase User"]),
#                     "&",
#                     ("category_id.name", "=", "Purchase"),
#                     ("name", "!=", "Manager"),
#                 ]
#             )
#             group_ids.extend(purchase_groups.ids)

#             # Additional purchase groups
#             purchase_xmlid_groups = [
#                 "purchase.group_purchase_user",  # Purchase User
#             ]

#             for xmlid in purchase_xmlid_groups:
#                 try:
#                     group = self.env.ref(xmlid, raise_if_not_found=False)
#                     if group:
#                         group_ids.append(group.id)
#                 except:
#                     pass

#         elif role == "warehouse":
#             # Warehouse/Inventory Groups
#             warehouse_groups = self.env["res.groups"].search(
#                 [
#                     "|",
#                     ("name", "in", ["User", "Warehouse User"]),
#                     "&",
#                     ("category_id.name", "=", "Inventory"),
#                     ("name", "!=", "Administrator"),
#                 ]
#             )
#             group_ids.extend(warehouse_groups.ids)

#             # Additional warehouse groups
#             warehouse_xmlid_groups = [
#                 "stock.group_stock_user",  # Inventory User
#                 "stock.group_stock_multi_locations",  # Multi Locations
#             ]

#             for xmlid in warehouse_xmlid_groups:
#                 try:
#                     group = self.env.ref(xmlid, raise_if_not_found=False)
#                     if group:
#                         group_ids.append(group.id)
#                 except:
#                     pass

#         elif role == "inventory":
#             # Inventory User
#             inventory_user = self.env.ref(
#                 "stock.group_stock_user", raise_if_not_found=False
#             )
#             if inventory_user:
#                 group_ids.append(inventory_user.id)

#         return list(set(group_ids))  # Remove duplicates

#     @api.model
#     def default_get(self, fields_list):
#         res = super(HrCreateUserWizard, self).default_get(fields_list)

#         # Get employee_id from context
#         if self._context.get("active_model") == "hr.employee" and self._context.get(
#             "active_id"
#         ):
#             res["employee_id"] = self._context.get("active_id")

#             # Check if employee already has a user_role set
#             employee = self.env["hr.employee"].browse(self._context.get("active_id"))
#             if hasattr(employee, "x_user_role") and employee.x_user_role:
#                 res["user_role"] = employee.x_user_role

#         return res

#     def action_create_user(self):
#         self.ensure_one()

#         # -----------------------------
#         # Validations
#         # -----------------------------
#         if self.password != self.confirm_password:
#             raise UserError("Passwords do not match.")

#         if not self.login:
#             raise UserError("Login is required.")

#         if not self.user_role_ids:
#             raise UserError("At least one role must be selected.")

#         # -----------------------------
#         # Check existing user
#         # -----------------------------
#         existing_user = self.env["res.users"].sudo().search(
#             [("login", "=", self.login)],
#             limit=1,
#         )
#         if existing_user:
#             raise UserError(f"A user with login '{self.login}' already exists.")

#         # -----------------------------
#         # Create user
#         # -----------------------------
#         user_vals = {
#             "name": self.employee_id.name,
#             "login": self.login,
#             "email": self.login,
#             "password": self.password,
#         }

#         user = self.env["res.users"].sudo().create(user_vals)

#         # -----------------------------
#         # Collect groups from ALL roles
#         # -----------------------------
#         group_ids = []
#         for role in self.user_role_ids:
#             group_ids.extend(self._get_groups_for_role(role.code))

#         group_ids = list(set(group_ids))  # dedupe

#         if group_ids:
#             user.sudo().write({
#                 "groups_id": [(6, 0, group_ids)]
#             })

#         # -----------------------------
#         # Link employee to user
#         # -----------------------------

#         self.employee_id.sudo().write({
#             "user_id": user.id
#         })

#         # -----------------------------
#         # Store roles on employee (if exists)
#         # -----------------------------
#         if hasattr(self.employee_id, "x_user_role_ids"):
#             self.employee_id.sudo().write({
#                 "x_user_role_ids": [(6, 0, self.user_role_ids.ids)]
#             })

#         return {
#             "type": "ir.actions.client",
#             "tag": "display_notification",
#             "params": {
#                 "title": "Success",
#                 "message": f"User created successfully for {self.employee_id.name}",
#                 "type": "success",
#                 "sticky": True,
#             },
#         }
