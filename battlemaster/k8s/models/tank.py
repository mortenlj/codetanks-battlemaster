from dataclasses import dataclass

from lightkube.core.dataclasses_dict import DataclassDictMixIn
from lightkube.models import meta_v1


@dataclass
class Owner(DataclassDictMixIn):
    name: str


@dataclass
class TankSpec(DataclassDictMixIn):
    image: str
    owner: Owner


@dataclass
class Tank(DataclassDictMixIn):
    apiVersion: str
    kind: str
    metadata: meta_v1.ObjectMeta
    spec: TankSpec
