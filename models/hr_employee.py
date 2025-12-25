from odoo import models, api
from odoo.exceptions import UserError

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def action_unlink_user(self):
        """Unlink and delete the user from the employee"""
        self.ensure_one()
        
        if not self.user_id:
            raise UserError("This employee has no linked user.")
        
        # Store user name for confirmation message
        user_name = self.user_id.name
        user_to_delete = self.user_id
        
        # Unlink the user from employee first
        self.write({'user_id': False})
        
        # Delete the user
        user_to_delete.sudo().unlink()
        
        # Return action to reload the current record
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': {
                'display_notification': {
                    'type': 'success',
                    'title': 'User Deleted',
                    'message': f'User "{user_name}" has been deleted.',
                    'sticky': False,
                }
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
