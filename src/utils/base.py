import pydantic
from typing import Generic, Iterator, TypeVar, List, Optional, get_type_hints

from src.dependencies.database import Database

T = TypeVar('T', bound="LegacyBaseModel")


class LegacyBaseModel(pydantic.BaseModel):
    @classmethod
    def doc_schema(cls):
        return {'application/json': cls.model_json_schema(ref_template="#/components/schemas/{model}")}

    @classmethod
    async def fetch(cls, db: Database, id_, *args, **kwargs) -> T:
        raise NotImplementedError("fetch() must be implemented in subclasses")

    @classmethod
    async def create(cls, db: Database, model: "LegacyBaseModel", *args, **kwargs) -> T:
        raise NotImplementedError("create() must be implemented in subclasses")

    async def update(self, db: Database, model: "LegacyBaseModel"):
        raise NotImplementedError("update() must be implemented in subclasses")


def optional_model(name: str, base: type[LegacyBaseModel]) -> type[LegacyBaseModel]:
    annotations = get_type_hints(base)
    optional_fields = {
        k: (Optional[v], None)
        for k, v in annotations.items()
    }
    return pydantic.create_model(name, **optional_fields, __base__=LegacyBaseModel)


class LegacyBaseList(pydantic.RootModel[List[T]], Generic[T]):
    root: List[T]

    def __iter__(self) -> Iterator[T]:
        return iter(self.root)

    def __getitem__(self, item) -> T:
        return self.root[item]

    @classmethod
    def doc_schema(cls):
        return {'application/json': cls.model_json_schema(ref_template="#/components/schemas/{model}")}

    @classmethod
    async def fetch(cls, db: Database, *args, **kwargs) -> "LegacyBaseList":
        raise NotImplementedError("fetch() must be implemented in subclasses")
