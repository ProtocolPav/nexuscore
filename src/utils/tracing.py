import functools
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


def traced(func=None, *, name: str = None):
    """
    Wraps an async service method in an OTel span.

    Usage:
        @traced
        async def get(self, ...): ...

        @traced(name="custom.span.name")
        async def get(self, ...): ...
    """
    if func is None:
        return functools.partial(traced, name=name)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        tracer = trace.get_tracer(func.__module__)
        span_name = name or func.__qualname__

        with tracer.start_as_current_span(span_name) as span:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    return wrapper