from __future__ import annotations

from fastapi import APIRouter, Depends

from adapters.inbound.api.dependencies import get_active_configuration, get_apply_configuration
from adapters.inbound.schemas.configuration_schemas import (
    ConfigResultResponse,
    ConfigurationPayload,
    ConfigurationResponse,
    RecipeResponse,
    ThresholdResponse,
)
from application.use_cases.apply_configuration import ApplyConfiguration
from application.use_cases.get_active_configuration import GetActiveConfiguration

router = APIRouter(prefix="/configuration", tags=["configuration"])


@router.get("", response_model=ConfigurationResponse)
def get_configuration(
    use_case: GetActiveConfiguration = Depends(get_active_configuration),
) -> ConfigurationResponse:
    """Return the currently active configuration (source, recipes, thresholds)."""
    view = use_case.execute()
    return ConfigurationResponse(
        source=view.source,
        waste_full_threshold=view.waste_full_threshold,
        recipes=[RecipeResponse(**vars(r)) for r in view.recipes],
        thresholds=[ThresholdResponse(**vars(t)) for t in view.thresholds],
    )


@router.post("", response_model=ConfigResultResponse)
def apply_configuration(
    body: ConfigurationPayload,
    use_case: ApplyConfiguration = Depends(get_apply_configuration),
) -> ConfigResultResponse:
    """
    Push a new configuration. All fields are optional (partial update).
    Returns 'accepted' or 'rejected' with a reason.
    """
    result = use_case.execute(body.model_dump(exclude_none=True))
    return ConfigResultResponse(
        status=result.status,
        source=result.source,
        reason=result.reason,
    )
