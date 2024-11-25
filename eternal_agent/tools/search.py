from typing import List
from eternal_agent.models import Tool, ToolParam, ToolParamDtype
from eternal_agent.registry import RegistryCategory, register_decorator
from . base_toolset import Toolset

from eternal_agent import constant as C
import requests

import re

def remove_html_tags(text: str) -> str:
    return re.sub(re.compile('<.*?>'), '', text)

def wiki_search(query: str, lang="en", top_k=C.DEFAULT_TOP_K) -> List[str]:
    headers = {
        'User-Agent': C.APP_NAME
    }
    url = f"https://api.wikimedia.org/core/v1/wikipedia/{lang}/search/page"
    params = {
        'q': query,
        'limit': top_k
    }
    
    resp = requests.get(url, headers=headers, params=params)

# @register_decorator(RegistryCategory.ToolSet)
class WikipediaSearch(Toolset):
    TOOLSET_NAME = "Wikipedia search"
    PURPOSE = "to retrieve data from Wikipedia"

    TOOLS: List[Tool] = [
        Tool(
            name="wiki_search",
            description="Search for something on Wikipedia",
            param_spec=[
                ToolParam(
                    name="query",
                    dtype=ToolParamDtype.STRING,
                    description="Query to search"
                )
            ],
            executor=lambda query: "Method not implemented"
        )
    ]