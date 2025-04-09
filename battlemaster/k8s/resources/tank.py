from lightkube.codecs import resource_registry
from lightkube.core import resource as res

from ..models import tank


@resource_registry.register
class Tank(res.NamespacedResourceG, tank.Tank):
    _api_info = res.ApiInfo(
        resource=res.ResourceDef('codetanks.ibidem.no', 'v1', 'Tank'),
        plural='tanks',
        verbs=[
            'delete', 'deletecollection', 'get', 'global_list', 'global_watch',
            'list', 'patch', 'post', 'put', 'watch'
        ],
    )
