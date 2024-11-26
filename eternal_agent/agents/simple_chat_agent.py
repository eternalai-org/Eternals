from .base_agent import InteractiveAgentBase
from eternal_agent.registry import register_decorator, RegistryCategory

@register_decorator(RegistryCategory.InteractiveAgent)
class SimpleChatAgent(InteractiveAgentBase):
    def __init__(self, cfg):
        pass