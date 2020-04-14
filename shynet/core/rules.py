import rules
from django.conf import settings


@rules.predicate
def is_service_creator(user):
    if settings.ONLY_SUPERUSERS_CREATE:
        return user.is_superuser
    return True


@rules.predicate
def is_service_owner(user, service):
    return service.owner == user


@rules.predicate
def is_service_collaborator(user, service):
    return service.collaborators.filter(pk=user.pk).exists()


rules.add_perm("core.view_service", is_service_owner | is_service_collaborator)
rules.add_perm("core.delete_service", is_service_owner)
rules.add_perm("core.change_service", is_service_owner)
rules.add_perm("core.create_service", is_service_creator)
