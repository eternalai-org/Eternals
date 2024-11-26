from typing import Any
from .character_base import CharacterBase
from eternal_agent.registry import register_decorator, RegistryCategory
from eternal_agent import constant as C

@register_decorator(RegistryCategory.CharacterBuilder)
class SimpleCharacterBuilder(CharacterBase):
    def __call__(self, characteristic_dict: dict) -> str:
        if "system_prompt" in characteristic_dict:
            return characteristic_dict["system_prompt"]
        
        characteristic_representation_template = '''
You are {name}, capable of executing any task assigned to you.

Here is a brief overview of your capabilities:    
{knowledge}

{bio}

{lore}

{interested_topics}'''

        personal_info = characteristic_dict.get("agent_personal_info", {})
        agent_name = personal_info.get("agent_name", "a highly intelligent AI assistant")

        bio_data, lore_data, knowledge_data = \
            characteristic_dict.get("bio", []),  \
            characteristic_dict.get("lore", []), \
            characteristic_dict.get("knowledge", [])

        bio_repr, lore_repr, knowledge_repr = "# Bio", "# Lore", "# Knowledge"

        for bio in bio_data[:C.DEFAULT_BIO_MAX_LENGTH]:
            bio_repr += f"\n- {bio}"

        for lore in lore_data[:C.DEFAULT_LORE_MAX_LENGTH]:
            lore_repr += f"\n- {lore}"
            
        for knowledge in knowledge_data[:C.DEFAULT_KNOWLEDGE_MAX_LENGTH]:
            knowledge_repr += f"\n- {knowledge}"
            
        interested_topics_data = characteristic_dict.get("interested_topics", [])
        interested_topics_repr = "# Interested Topics"
        
        for topic in interested_topics_data[:C.DEFAULT_INTERESTED_TOPICS_MAX_LENGTH]:
            interested_topics_repr += f"\n- {topic}"

        system_prompt = characteristic_representation_template.format(
            bio=bio_repr,
            lore=lore_repr,
            knowledge=knowledge_repr,
            interested_topics=interested_topics_repr,
            name=agent_name
        )
    
        return system_prompt
