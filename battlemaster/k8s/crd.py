import argparse
import importlib

import pyaml
from dc_schema import get_schema
from lightkube.core import resource
from lightkube.models import meta_v1
from lightkube.models.apiextensions_v1 import CustomResourceDefinitionSpec, CustomResourceDefinitionNames, \
    CustomResourceDefinitionVersion, CustomResourceValidation, CustomResourceSubresources, JSONSchemaProps
from lightkube.resources.apiextensions_v1 import CustomResourceDefinition


def _make_crd_schema(schema, defs=None):
    if defs is None:
        defs = {}
    crd_schema = {}
    defs.update(schema.get("$defs", {}))
    for key, value in schema.items():
        if key in ("$schema", "$defs", "default"):
            continue
        elif key == "$ref":
            ref = value.split('/')[-1]
            return defs[ref].copy()
        elif isinstance(value, dict):
            crd_schema[key] = _make_crd_schema(value, defs)
        elif isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, dict):
                    items.append(_make_crd_schema(item, defs))
                else:
                    items.append(item)
            crd_schema[key] = items
        else:
            crd_schema[key] = value
    return crd_schema


def crd(res: resource.Resource):
    """Given a Resource class, create the CustomResourceDefinition for it."""
    api_info = resource.api_info(res)

    scope = 'Namespaced' if issubclass(res, resource.NamespacedResource) else 'Cluster'

    schema = get_schema(res)
    crd_schema = JSONSchemaProps(**_make_crd_schema(schema))

    version = CustomResourceDefinitionVersion(
        name=api_info.resource.version,
        served=True,
        storage=True,
        schema=CustomResourceValidation(
            openAPIV3Schema=crd_schema,
        ),
        subresources=CustomResourceSubresources(
            status=dict()
        ),
    )

    crd = CustomResourceDefinition(
        apiVersion='apiextensions.k8s.io/v1',
        kind='CustomResourceDefinition',
        metadata=meta_v1.ObjectMeta(
            name=api_info.plural + '.' + api_info.resource.group,
        ),
        spec=CustomResourceDefinitionSpec(
            group=api_info.resource.group,
            names=CustomResourceDefinitionNames(
                kind=api_info.resource.kind,
                plural=api_info.plural,
                singular=api_info.resource.kind.lower(),
                shortNames=[],
            ),
            scope=scope,
            versions=[version],
        ),
    )

    pyaml.p(crd.to_dict())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('resource', type=str)
    args = parser.parse_args()
    package, resource = args.resource.rsplit('.', 1)
    m = importlib.import_module(package)
    res = getattr(m, resource)
    crd(res)


if __name__ == '__main__':
    main()
