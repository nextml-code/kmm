from pydantic import BaseModel, Extra


class FunctionalBase(BaseModel):
    class Config:
        allow_mutation = False
        extra = Extra.forbid

    def map(self, fn, *args, **kwargs):
        return fn(self, *args, **kwargs)

    def replace(self, **kwargs):
        new_dict = self.dict()
        new_dict.update(**kwargs)
        return type(self)(**new_dict)
