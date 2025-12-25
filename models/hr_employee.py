from odoo import models, api
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def action_unlink_user(self):
        """Unlink the user from the employee"""
        self.ensure_one()
        
        if not self.user_id:
            raise UserError("This employee has no linked user.")
        
        # Store user name for confirmation message
        user_name = self.user_id.name
        
        # Unlink the user
        self.write({'user_id': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'User Unlinked',
                'message': f'User "{user_name}" has been unlinked from this employee.',
                'type': 'success',
                'sticky': False,
            }
        }

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
