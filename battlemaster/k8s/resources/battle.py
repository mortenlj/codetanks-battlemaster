from typing import ClassVar

from lightkube.core import resource as res

from ..models import battle


class BattleStatus(res.NamespacedSubResource, battle.Battle):
    _api_info = res.ApiInfo(
        resource=res.ResourceDef('codetanks.ibidem.no', 'v1', 'Battle'),
        parent=res.ResourceDef('codetanks.ibidem.no', 'v1', 'Battle'),
        plural='battles',
        verbs=['get', 'patch', 'put'],
        action='status',
    )


class Battle(res.NamespacedResourceG, battle.Battle):
    _api_info = res.ApiInfo(
        resource=res.ResourceDef('codetanks.ibidem.no', 'v1', 'Battle'),
        plural='battles',
        verbs=['delete', 'deletecollection', 'get', 'global_list', 'global_watch', 'list', 'patch', 'post', 'put',
               'watch'],
    )

    Status: ClassVar = BattleStatus
