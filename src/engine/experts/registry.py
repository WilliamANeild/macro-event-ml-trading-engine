from __future__ import annotations

from typing import Type

from .base import BaseExpert
from .conflict_expert import ConflictEscalationExpert
from .crypto_expert import CryptoRegimeExpert
from .market_expert import MarketPricingExpert
from .mock_expert import MockExpert
from .rates_expert import RatesPolicyExpert
from .schemas import ExpertFamily
from .shipping_expert import ShippingChokePointExpert


# Central registry of all available experts
_EXPERT_REGISTRY: dict[str, Type[BaseExpert]] = {
    "conflict_escalation": ConflictEscalationExpert,
    "shipping_chokepoint": ShippingChokePointExpert,
    "rates_policy": RatesPolicyExpert,
    "market_pricing": MarketPricingExpert,
    "crypto_regime": CryptoRegimeExpert,
    "mock": MockExpert,
}

_FAMILY_TO_EXPERTS: dict[ExpertFamily, list[str]] = {
    ExpertFamily.CONFLICT_ESCALATION: ["conflict_escalation"],
    ExpertFamily.SHIPPING_CHOKEPOINT: ["shipping_chokepoint"],
    ExpertFamily.RATES_POLICY: ["rates_policy"],
    ExpertFamily.MARKET_PRICING: ["market_pricing"],
    ExpertFamily.CRYPTO_REGIME: ["crypto_regime"],
}


def get_experts(names: list[str] | None = None) -> list[BaseExpert]:
    """
    Instantiate experts by name.
    
    Args:
        names: Specific expert names to instantiate. If None, returns all.
        
    Returns:
        List of instantiated expert objects.
    """
    if names is None:
        names = list(_EXPERT_REGISTRY.keys())
    
    experts = []
    for name in names:
        if name in _EXPERT_REGISTRY:
            experts.append(_EXPERT_REGISTRY[name]())
    return experts


def get_expert_by_family(family: ExpertFamily) -> list[BaseExpert]:
    """
    Get all experts in a specific family.
    
    Args:
        family: The ExpertFamily enum value.
        
    Returns:
        List of expert instances for that family.
    """
    expert_names = _FAMILY_TO_EXPERTS.get(family, [])
    return get_experts(expert_names)


def get_available_experts() -> dict[str, str]:
    """Get mapping of expert names to their families."""
    result = {}
    for name, expert_cls in _EXPERT_REGISTRY.items():
        # Instantiate briefly to get family info
        instance = expert_cls()
        result[name] = instance.expert_family.value
    return result


def register_expert(name: str, expert_class: Type[BaseExpert]) -> None:
    """
    Register a new expert class.
    
    Args:
        name: Unique name for the expert.
        expert_class: Class inheriting from BaseExpert.
    """
    _EXPERT_REGISTRY[name] = expert_class


def get_expert_class(name: str) -> Type[BaseExpert] | None:
    """Get the expert class by name."""
    return _EXPERT_REGISTRY.get(name)
