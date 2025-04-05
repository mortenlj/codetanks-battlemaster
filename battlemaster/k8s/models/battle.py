from dataclasses import dataclass, field
from typing import Optional

from lightkube.core.dataclasses_dict import DataclassDictMixIn
from lightkube.models import meta_v1


@dataclass
class Server(DataclassDictMixIn):
    combatantUrl: str
    viewerUrl: str


@dataclass
class Combatant(DataclassDictMixIn):
    name: str


@dataclass
class BattleSpec(DataclassDictMixIn):
    combatants: list[Combatant]


@dataclass
class BattleStatus(DataclassDictMixIn):
    conditions: list[meta_v1.Condition] = field(default_factory=list)
    observedGeneration: Optional[int] = None
    server: Optional[Server] = None


@dataclass
class Battle(DataclassDictMixIn):
    apiVersion: str
    kind: str
    metadata: meta_v1.ObjectMeta
    spec: BattleSpec
    status: Optional[BattleStatus] = None
