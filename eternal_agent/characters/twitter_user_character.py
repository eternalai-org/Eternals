from typing import Any
from .character_base import CharacterBase
from eternal_agent.registry import register_decorator, RegistryCategory
from eternal_agent import constant as C

@register_decorator(RegistryCategory.CharacterBuilder)
class TwitterUserCharacterBuilder(CharacterBase):
    def __call__(self, characteristic_dict: dict) -> Any:
        if "system_prompt" in characteristic_dict:
            return characteristic_dict["system_prompt"]
        
        characteristic_representation_template = '''
You are {agent_name}, a highly intelligent agent, capable of executing any task assigned to you.

{knowledge}

About {agent_name} (@{twitter_username}):
{bio}

{lore}

{example_posts}

{interested_topics}

Again, your name is {agent_name}, and your twitter account is @{twitter_username}.
'''

        agent_personal_info = characteristic_dict.get("agent_personal_info", {})
        twitter_username = agent_personal_info.get("twitter_username", None)

        assert twitter_username is not None, "Twitter username is required"
        agent_name = agent_personal_info.get("agent_name", twitter_username)
        
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
            
        example_posts_data = characteristic_dict.get("example_posts", [])
        example_posts_repr = "# Example Posts"
        
        for post in example_posts_data[:C.DEFAULT_EXAMPLE_POSTS_MAX_LENGTH]:
            example_posts_repr += f"\n- {post}"
            
        interested_topics_data = characteristic_dict.get("interested_topics", [])
        interested_topics_repr = "# Interested Topics"
        
        for topic in interested_topics_data[:C.DEFAULT_INTERESTED_TOPICS_MAX_LENGTH]:
            interested_topics_repr += f"\n- {topic}"

        system_prompt = characteristic_representation_template.format(
            agent_name=agent_name,
            twitter_username=twitter_username,
            bio=bio_repr,
            lore=lore_repr,
            knowledge=knowledge_repr,
            example_posts=example_posts_repr,
            interested_topics=interested_topics_repr
        )
    
        return system_prompt