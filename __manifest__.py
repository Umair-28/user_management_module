{
    "name": "HR User Management",
    "version": "18.0.1.0.0",
    "category": "Human Resources",
    "summary": "Create system users from employees with password setup (no invite)",
    "description": """
HR User Management
==================
This module allows HR managers to create system users directly from
employee records by setting passwords manually instead of sending
invitation emails.

Features:
- Create user from employee with password
- Skip invitation email flow
- Secure password hashing
- HR-only access
""",
    "author": "Your Company Name",
    "website": "https://yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "hr",
        "base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/hr_user_role_data.xml",
        "views/create_user_wizard_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_user_role_views.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
