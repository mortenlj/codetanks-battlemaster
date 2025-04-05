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


def _eliminate_unwanted_keys(obj):
    if isinstance(obj, dict):
        crd_schema = {}
        for key, value in obj.items():
            if key in ("$schema", "$defs"):
                continue
            if key == "default" and not value:
                continue
            crd_schema[key] = _eliminate_unwanted_keys(value)
        return crd_schema
    elif isinstance(obj, list):
        return [_eliminate_unwanted_keys(item) for item in obj]
    return obj


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
        schema["required"].remove(ign) if ign in schema["required"] else None
    return schema


def _extract_defs(obj):
    defs = {}
    if isinstance(obj, dict):
        if "$defs" in obj:
            for key, value in obj["$defs"].items():
                defs[key] = value
            del obj["$defs"]
        for key, value in obj.items():
            defs.update(_extract_defs(value))
        return defs
    elif isinstance(obj, list):
        for item in obj:
            defs.update(_extract_defs(item))
    return defs


def crd(res: resource.Resource):
    """Given a Resource class, create the CustomResourceDefinition for it."""
    api_info = resource.api_info(res)

    scope = 'Namespaced' if issubclass(res, resource.NamespacedResource) else 'Cluster'

    schema = get_schema(res)
    schema = _drop_implicit(schema)
    defs = _extract_defs(schema)
    for key, item in defs.items():
        defs[key] = _resolve_refs(defs, item)
    schema = _resolve_refs(defs, schema)
    crd_schema = _eliminate_unwanted_keys(schema)
    crd_schema = _resolve_nullable(crd_schema)
    crd_schema = _resolve_single_all_ofs(crd_schema)
    json_schema_props = JSONSchemaProps(**crd_schema)

    version = CustomResourceDefinitionVersion(
        name=api_info.resource.version,
        served=True,
        storage=True,
        additionalPrinterColumns=[],
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
                categories=[],
            ),
            scope=scope,
            versions=[version],
        ),
    )

    pyaml.p(crd.to_dict(), vspacing=False)


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
