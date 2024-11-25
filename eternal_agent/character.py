from . import constant as C

# @TODO: modulize this

def build_character(characteristic_info: dict) -> str:
    characteristic_representation_template = '''
{knowledge}

About {agent_name} (@{twitter_username}):
{bio}

{lore}

{example_posts}

{interested_topics}'''

    agent_personal_info = characteristic_info.get("agent_personal_info", {})
    twitter_username = agent_personal_info.get("twitter_username", None)

    assert twitter_username is not None, "Twitter username is required"
    agent_name = agent_personal_info.get("agent_name", twitter_username)
    
    bio_data, lore_data, knowledge_data = \
        characteristic_info.get("bio", []),  \
        characteristic_info.get("lore", []), \
        characteristic_info.get("knowledge", [])
        
    bio_repr, lore_repr, knowledge_repr = "# Bio", "# Lore", "# Knowledge"

    for bio in bio_data[:C.DEFAULT_BIO_MAX_LENGTH]:
        bio_repr += f"\n- {bio}"

    for lore in lore_data[:C.DEFAULT_LORE_MAX_LENGTH]:
        lore_repr += f"\n- {lore}"
        
    for knowledge in knowledge_data[:C.DEFAULT_KNOWLEDGE_MAX_LENGTH]:
        knowledge_repr += f"\n- {knowledge}"
        
    example_posts_data = characteristic_info.get("example_posts", [])
    example_posts_repr = "# Example Posts"
    
    for post in example_posts_data[:C.DEFAULT_EXAMPLE_POSTS_MAX_LENGTH]:
        example_posts_repr += f"\n- {post}"
        
    interested_topics_data = characteristic_info.get("interested_topics", [])
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
