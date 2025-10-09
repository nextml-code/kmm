from pydantic import BaseModel, ConfigDict


class FunctionalBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    def map(self, fn, *args, **kwargs):
        return fn(self, *args, **kwargs)

    def replace(self, **kwargs):
        new_dict = self.model_dump()
        new_dict.update(**kwargs)
        return type(self)(**new_dict)
