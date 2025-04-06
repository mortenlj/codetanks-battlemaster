import types
from dataclasses import dataclass

from lightkube.core import resource


@dataclass
class ReconcilerConfig:
    resource: resource.Resource
    reconciler: types.ModuleType

    @property
    def name(self):
        return self.reconciler.__name__


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
