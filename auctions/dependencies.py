import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Any
from typing import Callable
from typing import Generic
from typing import TypeVar
from typing import TYPE_CHECKING

from flask import has_request_context
from flask import request

if TYPE_CHECKING:
    from auctions.utils.app import Flask


DependencyInstance = TypeVar("DependencyInstance", bound=object)


@dataclass
class Dependency(Generic[DependencyInstance]):
    class_name: str
    class_: type[DependencyInstance]
    depends: list["Dependency"]
    arg_name: str | None = None


class Provide:
    ...


class GlobalStorage:
    def __init__(self) -> None:
        self._storage = {}

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def has(self, key: str) -> bool:
        if has_request_context() and hasattr(request, key):
            return True

        return key in self._storage

    def get(self, key: str, default: Any | None = None) -> Any:
        if has_request_context() and hasattr(request, key):
            return getattr(request, key)

        return self._storage.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if has_request_context():
            setattr(request, key, value)
            return

        self._storage[key] = value

    def delete(self, key) -> None:
        if has_request_context() and hasattr(request, key):
            delattr(request, key)

        if key in self._storage:
            del self._storage[key]


class DependencyProvider:
    def __init__(self, app: "Flask") -> None:
        self.app = app
        self.storage = GlobalStorage()
        self._cache = {}

    def add_global(self, obj: object) -> None:
        self.storage.set(self.get_qual_name(obj.__class__), obj)

    def remove_global(self, obj: object) -> None:
        self.storage.delete(self.get_qual_name(obj.__class__))

    @staticmethod
    def get_qual_name(cls: type) -> str:
        if cls.__module__ == "builtins":
            return cls.__qualname__

        return f"{cls.__module__}.{cls.__qualname__}"

    def resolve_dependency_tree(self, func_or_cls: Callable) -> list[Dependency]:
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
        local_deps: dict[str, object] | list | None = None,
    ) -> DependencyInstance:
        local_deps = local_deps or {}

        if isinstance(local_deps, list):
            local_deps = {self.get_qual_name(dep.__class__): dep for dep in (local_deps or [])}

        if not isinstance(dependency, Dependency):
            return self.provide(
                Dependency(
                    class_name=self.get_qual_name(dependency),
                    class_=dependency,
                    depends=self.resolve_dependency_tree(dependency),
                ),
                local_deps,
            )

        if dependency.class_name in local_deps:
            return local_deps[dependency.class_name]

        if dependency.class_name in self.storage:
            return self.storage.get(dependency.class_name)

        if dependency.class_name in self._cache:
            return self._cache[dependency.class_name]

        dep_kwargs = {}

        for sub_dependency in dependency.depends:
            dep_instance = self.provide(sub_dependency, local_deps)
            dep_kwargs[sub_dependency.arg_name] = dep_instance
            self._cache[sub_dependency.class_name] = dep_instance

        return dependency.class_(**dep_kwargs)

    def invalidate_cache(self, dependency: Dependency) -> None:
        if dependency.class_name in self._cache:
            del self._cache[dependency.class_name]

        for sub_dependency in dependency.depends:
            self.invalidate_cache(sub_dependency)

    def inject(self, func: Callable, local_deps: dict | list | None = None) -> Callable:
        if isinstance(local_deps, list):
            local_deps = {self.get_qual_name(dep.__class__): dep for dep in (local_deps or [])}

        dependency_tree = self.resolve_dependency_tree(func)

        @wraps(func)
        def decorated(*args, **kwargs):
            dep_kwargs = {}

            for dependency in dependency_tree:
                dep_kwargs[dependency.arg_name] = self.provide(dependency, local_deps)

            result = func(*args, **kwargs, **dep_kwargs)

            for dependency in dependency_tree:
                self.invalidate_cache(dependency)

            return result

        return decorated
