from odoo import models, api

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def action_open_create_user_wizard(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Create New User",
            "res_model": "hr.create.user.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_employee_id": self.id,
                "default_login": self.work_email,
            },
        }
