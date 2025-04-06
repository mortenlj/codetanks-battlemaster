import typing
from abc import abstractmethod
from dataclasses import dataclass

from lightkube.core import resource


@dataclass
class Key:
    name: str
    namespace: str

    @classmethod
    def from_obj(cls, obj):
        return cls(obj.metadata.name, obj.metadata.namespace)

    def __str__(self):
        return f"{self.name}.{self.namespace}"

    def __repr__(self):
        return f"Key({self.name}, {self.namespace})"


class Reconciler(typing.Protocol):
    @abstractmethod
    async def reconcile(self, key: Key):
        """Reconcile the resource with the given key."""
        raise NotImplementedError()


@dataclass
class ReconcilerConfig:
    name: str
    resource: resource.Resource
    reconciler: Reconciler
