from __future__ import annotations

from fastapi import APIRouter, Depends

from adapters.inbound.api.dependencies import (
    get_all_container_states,
    get_container_state,
    get_empty_waste,
    get_fill_container,
)
from adapters.inbound.schemas.container_schemas import (
    AllContainersResponse,
    ContainerStateResponse,
    FillRequest,
    WasteStateResponse,
)
from application.use_cases.empty_waste import EmptyWaste
from application.use_cases.fill_container import FillContainer
from application.use_cases.get_container_state import GetAllContainerStates, GetContainerState
from domain.model.value_objects import ContainerId

router = APIRouter(prefix="/containers", tags=["operator"])


@router.get("", response_model=AllContainersResponse)
def list_all_containers(
    use_case: GetAllContainerStates = Depends(get_all_container_states),
) -> AllContainersResponse:
    """Return the current state of all ingredient containers and the waste container."""
    ingredients, waste = use_case.execute()
    return AllContainersResponse(
        ingredients=[ContainerStateResponse(**vars(c)) for c in ingredients],
        waste=WasteStateResponse(**vars(waste)),
    )


@router.get("/{container_id}", response_model=ContainerStateResponse)
def get_container(
    container_id: ContainerId,
    use_case: GetContainerState = Depends(get_container_state),
) -> ContainerStateResponse:
    """Return the current state of one ingredient container."""
    view = use_case.execute(container_id)
    return ContainerStateResponse(**vars(view))


@router.put("/{container_id}/fill", response_model=ContainerStateResponse)
def fill_container(
    container_id: ContainerId,
    body: FillRequest,
    use_case: FillContainer = Depends(get_fill_container),
) -> ContainerStateResponse:
    """Fill an ingredient container to the given target level."""
    view = use_case.execute(container_id, body.target_level)
    return ContainerStateResponse(**vars(view))


@router.delete("/waste", response_model=WasteStateResponse)
def empty_waste(
    use_case: EmptyWaste = Depends(get_empty_waste),
) -> WasteStateResponse:
    """Empty the waste container and reset brew count to zero."""
    view = use_case.execute()
    return WasteStateResponse(**vars(view))
