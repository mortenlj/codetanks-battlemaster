from dataclasses import dataclass
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
    observedGeneration: int
    conditions: list[meta_v1.Condition]
    server: Optional[Server] = None


@dataclass
class Battle(DataclassDictMixIn):
    apiVersion: str
    kind: str
    metadata: meta_v1.ObjectMeta
    spec: BattleSpec
    status: Optional[BattleStatus] = None
