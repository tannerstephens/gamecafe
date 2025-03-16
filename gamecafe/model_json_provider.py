from flask.json.provider import DefaultJSONProvider

from .models import IdModel


class ModelJsonProvider(DefaultJSONProvider):
    def default(self, o: object):
        if isinstance(o, IdModel):
            return o.serialize()

        if isinstance(o, IdModel.Page):
            return o.serialize()

        if hasattr(o, "serialize"):
            return o.serialize()

        return super().default(o)
