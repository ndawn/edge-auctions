import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Generic
from typing import Self
from typing import TypeVar

from flask import Flask


GLOBALS = {}


DependencyInstance = TypeVar("DependencyInstance", bound=object)


@dataclass
class Dependency(Generic[DependencyInstance]):
    arg_name: str
    class_name: str
    class_: type[DependencyInstance]
    depends: list["Dependency"]


class Provide:
    ...


class DependencyProvider:
    instance: Self = None

    def __new__(cls, app: Flask) -> "DependencyProvider":
        if cls.instance is None:
            cls.instance = super().__new__(cls)

        return cls.instance

    def __init__(self, app: Flask) -> None:
        self.app = app
        self._cache = {}

    def add_global(self, obj: ...) -> None:
        GLOBALS[self.get_qual_name(obj.__class__)] = obj

    @staticmethod
    def get_qual_name(cls: type) -> str:
        if cls.__module__ == "builtins":
            return cls.__qualname__

        return f"{cls.__module__}.{cls.__qualname__}"

    def resolve_dependency_tree(self, func_or_cls: callable) -> list[Dependency]:
        signature = inspect.signature(func_or_cls)

        return [
            Dependency(
                arg_name=arg_name,
                class_name=self.get_qual_name(arg_value.annotation),
                class_=arg_value.annotation,
                depends=self.resolve_dependency_tree(arg_value.annotation),
            )
            for arg_name, arg_value in signature.parameters.items()
            if (
                isinstance(arg_value.default, Provide)
                and not isinstance(arg_value.annotation, inspect.Parameter.empty)
            )
        ]

    def provide(
        self,
        dependency: Dependency[DependencyInstance] | type[DependencyInstance],
    ) -> DependencyInstance:
        if not isinstance(dependency, Dependency):
            return self.provide(Dependency("", self.get_qual_name(dependency), dependency, []))

        if dependency.class_name in GLOBALS:
            return GLOBALS[dependency.class_name]

        if dependency.class_name in self._cache:
            return self._cache[dependency.class_name]

        dep_kwargs = {}

        for sub_dependency in dependency.depends:
            dep_instance = self.provide(sub_dependency)
            dep_kwargs[sub_dependency.arg_name] = dep_instance
            self._cache[sub_dependency.class_name] = dep_instance

        return dependency.class_(**dep_kwargs)

    def invalidate_cache(self, dependency: Dependency) -> None:
        if dependency.class_name in self._cache:
            del self._cache[dependency.class_name]

        for sub_dependency in dependency.depends:
            self.invalidate_cache(sub_dependency)


def inject(func: callable) -> callable:
    if DependencyProvider.instance is None:
        raise RuntimeError("Dependency provider is not instantiated")

    provider = DependencyProvider.instance
    dependency_tree = provider.resolve_dependency_tree(func)

    @wraps(func)
    def decorated(*args, **kwargs):
        dep_kwargs = {}

        for dependency in dependency_tree:
            dep_kwargs[dependency.arg_name] = provider.provide(dependency)

        app = provider.provide(Flask)

        with app.app_context():
            result = func(*args, **kwargs, **dep_kwargs)

        for dependency in dependency_tree:
            provider.invalidate_cache(dependency)

        return result

    return decorated
