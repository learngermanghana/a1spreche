"""Flask health check route registration."""

from flask import Flask


def register_health_route(app: Flask) -> None:
    @app.get("/health")
    def health():  # pragma: no cover - trivial
        return {"ok": True}, 200

__all__ = ["register_health_route"]
