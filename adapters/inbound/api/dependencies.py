from __future__ import annotations

from fastapi import Request

from application.use_cases.apply_configuration import ApplyConfiguration
from application.use_cases.brew_beverage import BrewBeverage
from application.use_cases.empty_waste import EmptyWaste
from application.use_cases.fill_container import FillContainer
from application.use_cases.get_active_configuration import GetActiveConfiguration
from application.use_cases.get_container_state import GetAllContainerStates, GetContainerState


# Each function reads shared state from app.state (wired in main.py at startup).
# Tests override app.state with in-memory stubs — no mocking framework needed.

def get_brew_beverage(request: Request) -> BrewBeverage:
    s = request.app.state
    return BrewBeverage(s.container_repo, s.config, s.machine, s.alerts, s.display)


def get_fill_container(request: Request) -> FillContainer:
    s = request.app.state
    return FillContainer(s.container_repo, s.config, s.machine, s.alerts, s.display)


def get_empty_waste(request: Request) -> EmptyWaste:
    s = request.app.state
    return EmptyWaste(s.container_repo, s.machine, s.display)


def get_apply_configuration(request: Request) -> ApplyConfiguration:
    s = request.app.state
    return ApplyConfiguration(s.config, s.container_repo)


def get_container_state(request: Request) -> GetContainerState:
    return GetContainerState(request.app.state.container_repo)


def get_all_container_states(request: Request) -> GetAllContainerStates:
    return GetAllContainerStates(request.app.state.container_repo)


def get_active_configuration(request: Request) -> GetActiveConfiguration:
    return GetActiveConfiguration(request.app.state.config)
