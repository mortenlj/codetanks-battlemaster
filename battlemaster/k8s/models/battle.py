from typing import Optional

from lightkube.core.schema import DictMixin, dataclass
from lightkube.models import meta_v1


@dataclass
class Server(DictMixin):
    combatantUrl: str
    viewerUrl: str


@dataclass
class Combatant(DictMixin):
    name: str


@dataclass
class BattleSpec(DictMixin):
    combatants: list[Combatant]


@dataclass
class BattleStatus(DictMixin):
    conditions: Optional[list[meta_v1.Condition]] = None
    observedGeneration: Optional[int] = None
    server: Optional[Server] = None


@dataclass
class Battle(DictMixin):
    apiVersion: Optional[str] = None
    kind: Optional[str] = None
    metadata: Optional[meta_v1.ObjectMeta] = None
    spec: Optional[BattleSpec] = None
    status: Optional[BattleStatus] = None
