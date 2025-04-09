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
    conditions: Optional[list[meta_v1.Condition]] = None
    observedGeneration: Optional[int] = None
    server: Optional[Server] = None


@dataclass
class Battle(DataclassDictMixIn):
    apiVersion: Optional[str] = None
    kind: Optional[str] = None
    metadata: Optional[meta_v1.ObjectMeta] = None
    spec: Optional[BattleSpec] = None
    status: Optional[BattleStatus] = None
