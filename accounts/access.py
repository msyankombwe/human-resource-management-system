from django.db.models import Q

from employees.models import Employee


def visible_employees(user):
    """Return the employee records a signed-in user's role may view."""
    employees = Employee.objects.select_related('user', 'department', 'manager')
    profile = getattr(user, 'profile', None)
    if profile and profile.role in {'ADMIN', 'HR'}:
        return employees

    employee = getattr(user, 'employee', None)
    if not employee:
        return employees.none()
    if profile and profile.role == 'MANAGER':
        return employees.filter(Q(pk=employee.pk) | Q(manager=employee))
    if profile and profile.role == 'EMPLOYEE':
        return employees.filter(pk=employee.pk)
    return employees.none()
