from typing import Optional

from lightkube.core.schema import DictMixin, dataclass
from lightkube.models import meta_v1


@dataclass
class Owner(DictMixin):
    name: str


@dataclass
class TankSpec(DictMixin):
    image: str
    owner: Owner


@dataclass
class Tank(DictMixin):
    apiVersion: Optional[str] = None
    kind: Optional[str] = None
    metadata: Optional[meta_v1.ObjectMeta] = None
    spec: Optional[TankSpec] = None
