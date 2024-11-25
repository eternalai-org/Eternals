from typing import Any
from eternal_agent.models import AgentLog

class InteractiveAgentBase(object):
    def __init__(self, *args, **kwargs) -> None:
        pass

    def __call__(self, log: AgentLog) -> AgentLog:
        raise NotImplementedError("You must implement this method in your subclass")

class NonInteractiveAgentBase(object):
    def __init__(self, *args, **kwargs) -> None:
        pass

    def __call__(self, log: AgentLog) -> AgentLog:
        raise NotImplementedError("You must implement this method in your subclass")