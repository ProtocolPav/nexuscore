import functools
import inspect
from fastapi import HTTPException
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

    span_name = name or func.__qualname__

    def _handle_exception(span, e: Exception):
        if isinstance(e, HTTPException) and 400 <= e.status_code < 500:
            # Expected client-facing outcome (NotFound, BadRequest, etc.)
            # Still record it as an event for visibility, but don't flag the span as an error.
            span.set_attribute("http.status_code", e.status_code)
            span.add_event("expected_error", {"exception.message": str(e.detail)})
        else:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)

    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(func.__module__)
            with tracer.start_as_current_span(span_name) as span:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    _handle_exception(span, e)
                    raise
        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        tracer = trace.get_tracer(func.__module__)
        with tracer.start_as_current_span(span_name) as span:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _handle_exception(span, e)
                raise
    return sync_wrapper