from typing import Any
from eternal_agent.models import AgentLog, NonInteractiveAgentLog, ChainState, Mission, AssistantResponse

class InteractiveAgentBase(object):
    def __init__(self, log: AgentLog) -> None:
        self.log = log
        
    @property
    def id(self) -> str:
        return self.log.id

    def step(self, mission: Mission) -> AssistantResponse:
        resp = self.__call__(mission)
        
        assert resp.scratchpad[-1]['role'] == 'assistant'
        
        return AssistantResponse(
            content=resp.scratchpad[-1]['content']
        )

    def __call__(self, log: Mission) -> AgentLog:
        raise NotImplementedError("You must implement this method in your subclass")

class NonInteractiveAgentBase(object):
    def __init__(self, log: NonInteractiveAgentLog) -> None:
        self.log = log
        
    @property
    def id(self) -> str:
        return self.log.id

    @property
    def state(self) -> ChainState:
        return self.log.state

    def step(self) -> NonInteractiveAgentLog:
        if self.log.state == ChainState.NEW or self.log.state == ChainState.RUNNING:
            return self.__call__()

        return self.log

    def __call__(self) -> NonInteractiveAgentLog:
        raise NotImplementedError("You must implement this method in your subclass")