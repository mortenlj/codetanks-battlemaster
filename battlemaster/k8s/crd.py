import argparse
import importlib

import pyaml
from dc_schema import get_schema
from lightkube.core import resource
from lightkube.models import meta_v1
from lightkube.models.apiextensions_v1 import CustomResourceDefinitionSpec, CustomResourceDefinitionNames, \
    CustomResourceDefinitionVersion, CustomResourceValidation, CustomResourceSubresources, JSONSchemaProps
from lightkube.resources.apiextensions_v1 import CustomResourceDefinition


def _resolve_refs(defs, value):
    if isinstance(value, dict):
        if "$ref" in value:
            ref = value["$ref"].split('/')[-1]
            return defs[ref]
        for key, val in value.items():
            value[key] = _resolve_refs(defs, val)
    elif isinstance(value, list):
        for i, val in enumerate(value):
            value[i] = _resolve_refs(defs, val)
    return value


def _make_crd_schema(schema, defs=None):
    if defs is None:
        defs = {}
    crd_schema = {}
    defs.update(schema.get("$defs", {}))
    for key, value in defs.items():
        defs[key] = _resolve_refs(defs, value)
    if isinstance(schema, dict) and "$ref" in schema:
        return _resolve_refs(defs, schema)
    for key, value in schema.items():
        if key in ("$schema", "$defs", "default"):
            continue
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


def _resolve_nullable(obj):
    result = {}
    if isinstance(obj, dict):
        nullable = False
        if "anyOf" in obj:
            candidate = None
            for item in obj["anyOf"]:
                if item.get("type") == "null":
                    nullable = True
                else:
                    candidate = item
            if nullable:
                result = _resolve_nullable(candidate)
                result["nullable"] = True
        for key, value in obj.items():
            if nullable and key == "anyOf":
                continue
            result[key] = _resolve_nullable(value)
    elif isinstance(obj, list):
        result = [_resolve_nullable(value) for value in obj]
    else:
        result = obj
    return result


def _resolve_single_all_ofs(obj):
    result = {}
    if isinstance(obj, dict):
        if "allOf" in obj and len(obj["allOf"]) == 1:
            result = _resolve_single_all_ofs(obj["allOf"][0])
            del obj["allOf"]
        for key, value in obj.items():
            result[key] = _resolve_single_all_ofs(value)
    elif isinstance(obj, list):
        result = [_resolve_single_all_ofs(value) for value in obj]
    else:
        result = obj
    return result


def _drop_implicit(schema: dict):
    """Kubernetes assumes all schemas have apiVersion, kind and metadata, so they should be dropped."""
    for ign in ("apiVersion", "kind", "metadata"):
        schema["properties"].pop(ign, None)
    return schema


def crd(res: resource.Resource):
    """Given a Resource class, create the CustomResourceDefinition for it."""
    api_info = resource.api_info(res)

    scope = 'Namespaced' if issubclass(res, resource.NamespacedResource) else 'Cluster'

    schema = get_schema(res)
    schema = _drop_implicit(schema)
    crd_schema = _make_crd_schema(schema)
    crd_schema = _resolve_nullable(crd_schema)
    crd_schema = _resolve_single_all_ofs(crd_schema)
    json_schema_props = JSONSchemaProps(**crd_schema)

    version = CustomResourceDefinitionVersion(
        name=api_info.resource.version,
        served=True,
        storage=True,
        schema=CustomResourceValidation(
            openAPIV3Schema=json_schema_props,
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
