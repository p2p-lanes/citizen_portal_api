"""Citizen Portal API Application."""


def setup_model_relationships():
    """Initialize relationships between models to resolve circular dependencies."""
    from app.api.applications.models import (
        setup_relationships as setup_app_relationships,
    )

    setup_app_relationships()


# Initialize relationships after models are defined
setup_model_relationships()
