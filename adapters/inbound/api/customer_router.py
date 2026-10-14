from __future__ import annotations

from fastapi import APIRouter, Depends

from adapters.inbound.api.dependencies import get_active_configuration, get_brew_beverage
from adapters.inbound.schemas.beverage_schemas import (
    BeverageItem,
    BeverageListResponse,
    BrewRequest,
    BrewResponse,
)
from application.use_cases.brew_beverage import BrewBeverage
from application.use_cases.get_active_configuration import GetActiveConfiguration

router = APIRouter(prefix="/beverages", tags=["customer"])


@router.get("", response_model=BeverageListResponse)
def list_beverages(
    use_case: GetActiveConfiguration = Depends(get_active_configuration),
) -> BeverageListResponse:
    """List all available beverages from the active configuration."""
    config = use_case.execute()
    return BeverageListResponse(
        beverages=[BeverageItem(beverage_id=r.beverage_id, name=r.name) for r in config.recipes]
    )


@router.post("/brew", response_model=BrewResponse, status_code=200)
def brew_beverage(
    body: BrewRequest,
    use_case: BrewBeverage = Depends(get_brew_beverage),
) -> BrewResponse:
    """Request a beverage brew. Validates ingredient levels and machine state."""
    result = use_case.execute(body.beverage_id)
    return BrewResponse(
        brew_order_id=result.brew_order_id,
        beverage_id=result.beverage_id,
        status=result.status,
    )
