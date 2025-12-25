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
    groups_id = fields.Many2many(
        "res.groups",
        string="Access Rights",
        help="Select the access rights/groups for this user"
    )

    def action_create_user(self):
        self.ensure_one()

        if self.password != self.confirm_password:
            raise UserError("Passwords do not match.")

        if not self.login:
            raise UserError("Login is required.")

        # Create user with password and groups
        user = self.env["res.users"].sudo().create({
            "name": self.employee_id.name,
            "login": self.login,
            "email": self.login,
            "password": self.password,
            "groups_id": [(6, 0, self.groups_id.ids)],  # Set groups
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

#     def action_create_user(self):
#         self.ensure_one()

#         if self.password != self.confirm_password:
#             raise UserError("Passwords do not match.")

#         if not self.login:
#             raise UserError("Login is required.")

#         # Create user with password
#         user = self.env["res.users"].sudo().create({
#             "name": self.employee_id.name,
#             "login": self.login,
#             "email": self.login,
#             "password": self.password,  # Set password during creation
#         })

#         # Link employee to user
#         self.employee_id.sudo().write({
#             "user_id": user.id
#         })

#         return {"type": "ir.actions.act_window_close"}