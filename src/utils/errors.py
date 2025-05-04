from sanic import BadRequest, Forbidden
from sanic.exceptions import SanicException, NotFound


class NotFound404(NotFound):
    @property
    def message(self):
        return f"Could not find a {self.extra['resource']} with ID {self.extra['id']}."


class BadRequest400(BadRequest):
    @property
    def message(self):
        return f"Bad request. Check the data you provided."


class Forbidden403(Forbidden):
    @property
    def message(self):
        return f"Could not process this request. It is forbidden."