"""
wc2026.live — live in-match PMF engine.

Modules
-------
state       MatchState dataclass: current score, clock, events, stats
features    Feature extraction from MatchState → LiveFeatureVector
hazard      Non-homogeneous minute-level goal hazard model
predictor   LivePMFPredictor: score-state PMF updated every minute
replay      2022 match replay engine (minute-by-minute)
validation  Replay validation metrics and reports
"""
from .state import MatchState, MatchStatus, EventType, MatchEvent
from .features import LiveFeatureVector, extract_features
from .predictor import LivePMFPredictor

__all__ = [
    "MatchState", "MatchStatus", "EventType", "MatchEvent",
    "LiveFeatureVector", "extract_features",
    "LivePMFPredictor",
]
