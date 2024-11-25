import json

# this class is simply a system prompt builder
class CharacterBase(object):
    def __call__(self, characteristic_dict: dict) -> str:
        return "You are a highly intelligent agent, capable of executing any task assigned to you."