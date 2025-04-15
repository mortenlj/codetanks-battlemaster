import asyncio
from typing import Annotated

import dagger
import toml
from dagger import dag, function, object_type, DefaultPath, Ignore
from jinja2 import Template

DEVELOP_IMAGE = "ttl.sh/mortenlj-battlemaster"
DEVELOP_VERSION = "1h"


@object_type
class CodetanksBattlemaster:
    source: Annotated[dagger.Directory, DefaultPath("/"), Ignore(["target", ".github", "dagger", ".idea"])]

    async def resolve_python_version(self) -> str:
        """Resolve the Python version"""
        contents = await self.source.file("pyproject.toml").contents()
        pyproject = toml.loads(contents)
        py_version = pyproject["project"]["requires-python"]
        return py_version[2:]

    async def install_mise(self, container: dagger.Container, *tools) -> dagger.Container:
        """Install Mise in a container, and install tools"""
        installer = dag.http("https://mise.run")
        return (
            container
            .with_exec(["apt-get", "update", "--yes"])
            .with_exec(["apt-get", "install", "--yes", "curl"])
            .with_env_variable("MISE_DATA_DIR", "/mise")
            .with_env_variable("MISE_CONFIG_DIR", "/mise")
            .with_env_variable("MISE_CACHE_DIR", "/mise/cache")
            .with_env_variable("MISE_INSTALL_PATH", "/usr/local/bin/mise")
            .with_env_variable("PATH", "/mise/shims:${PATH}", expand=True)
            .with_new_file("/usr/local/bin/mise-installer", await installer.contents(), permissions=755)
            .with_exec(["/usr/local/bin/mise-installer"])
            .with_exec(["mise", "trust", "/app/mise.toml"])
            .with_file("/app/mise.toml", self.source.file(".config/mise/config.toml"))
            .with_exec(["mise", "install", *tools])
        )

    @function
    async def deps(self, platform: dagger.Platform | None = None) -> dagger.Container:
        """Install dependencies in a container"""
        python_version = await self.resolve_python_version()
        base_container = dag.container(platform=platform).from_(f"python:{python_version}-slim").with_workdir("/app")
        return (
            (await self.install_mise(base_container, "uv"))
            .with_exec(["apt-get", "--yes", "update"])
            .with_exec(["apt-get", "--yes", "install", "cmake", "musl-tools", "gcc"])
            .with_file("/app/pyproject.toml", self.source.file("pyproject.toml"))
            .with_file("/app/uv.lock", self.source.file("uv.lock"))
            .with_exec(["uv", "sync", "--no-install-workspace", "--locked", "--compile-bytecode"])
        )

    @function
    async def build(self, platform: dagger.Platform | None = None, version: str = DEVELOP_VERSION) -> dagger.Container:
        """Build the application"""
        return (
            (await self.deps(platform))
            .with_directory("/app/battlemaster", self.source.directory("battlemaster"))
            .with_file("/app/README.rst", self.source.file("README.rst"))
            .with_new_file("/app/battlemaster/__init__.py", f"VERSION = \"1.{version.replace("-", "+")}\"")
            .with_exec(["uv", "sync", "--frozen", "--no-editable"])
        )

    @function
    async def docker(self, platform: dagger.Platform | None = None, version: str = DEVELOP_VERSION) -> dagger.Container:
        """Build the Docker container"""
        python_version = await self.resolve_python_version()
        deps = await self.deps(platform)
        src = await self.build(platform, version)
        return (
            dag.container(platform=platform)
            .from_(f"python:{python_version}-slim")
            .with_workdir("/app")
            .with_directory("/app/.venv", deps.directory("/app/.venv"))
            .with_directory("/app/battlemaster", src.directory("/app/battlemaster"))
            .with_env_variable("PATH", "/app/.venv/bin:${PATH}", expand=True)
            .with_entrypoint(["/app/.venv/bin/python", "-m", "battlemaster"])
        )

    @function
    async def publish(self, image: str = DEVELOP_IMAGE, version: str = DEVELOP_VERSION) -> str:
        """Publish the application container after building and testing it on-the-fly"""
        platforms = [
            dagger.Platform("linux/amd64"),  # a.k.a. x86_64
            dagger.Platform("linux/arm64"),  # a.k.a. aarch64
        ]
        cos = []
        manifest = dag.container()
        published = []
        versions = [version]
        if version != DEVELOP_VERSION:
            versions.append("latest")
        for v in versions:
            variants = []
            for platform in platforms:
                variants.append(await self.docker(platform))
            published.append(await manifest.publish(f"{image}:{v}", platform_variants=variants))

        return "\n".join(published)

    @function
    async def crd(self) -> dagger.File:
        """Generate CRD"""
        build = await self.build(await dag.default_platform())
        return (
            build
            .with_exec(["uv", "run", "crd", "battlemaster.k8s.resources.battle.Battle"], redirect_stdout="battle.yaml")
            .file("battle.yaml")
        )

    @function
    async def assemble_manifests(self, image: str = DEVELOP_IMAGE,
                                 version: str = DEVELOP_VERSION) -> dagger.File:
        """Assemble manifests"""
        template_dir = self.source.directory("deploy")
        documents = []
        for filepath in await template_dir.entries():
            src = await template_dir.file(filepath).contents()
            if not filepath.endswith(".j2"):
                contents = src
            else:
                template = Template(src, enable_async=True)
                contents = await template.render_async(image=image, version=version)
            if contents.startswith("---"):
                documents.append(contents)
            else:
                documents.append("---\n" + contents)
        return await self.source.with_new_file("deploy.yaml", "\n".join(documents)).file("deploy.yaml")

    @function
    async def assemble(
            self,
            image: str = DEVELOP_IMAGE,
            version: str = DEVELOP_VERSION
    ) -> dagger.Directory:
        """Collect all deployment artifacts (container, crd and manifests)"""
        outputs = dag.directory()
        files = await asyncio.gather(
            self.publish_to_file(self.publish(image, version)),
            self.crd(),
            self.assemble_manifests(image, version),
        )
        for f in files:
            filename = await f.name()
            outputs = outputs.with_file(filename, f)
        return outputs

    @staticmethod
    async def publish_to_file(publish_task) -> dagger.File:
        image_tags = await publish_task
        return (
            dag.directory()
            .with_new_file("image_tags.txt", image_tags)
            .file("image_tags.txt")
        )
