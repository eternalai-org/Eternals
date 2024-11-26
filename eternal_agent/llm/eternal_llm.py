from .base_llm import AsyncChatCompletion
from eternal_agent.registry import RegistryCategory, register_decorator
from typing import List, Dict
import logging
from eternal_agent.models import InferenceResult, InferenceState
import requests
from eternal_agent import constant as C

logger = logging.getLogger(__name__)

# TODO: convert the openai standard to async standard of eternal AI 
@register_decorator(RegistryCategory.LLM)
class EternalAIChatCompletion(AsyncChatCompletion):
    DEFAULT_PARAMS = {
        "top_p": 1.0,
        "presence_penalty": 0.0,
        "n": 1,
        "logit_bias": None,
        "frequency_penalty": 0.0,
    }

    def __call__(self, _messages: List[Dict[str, str]], stop: List[str]=[], override_kwargs: dict={}): 

        for _try in range(self.max_retries + 1):
            if _try > 0:
                logger.warning("Retrying {} out of {}".format(_try, self.max_retries))

            payload = {
                **self.model_kwargs,
                **self.DEFAULT_PARAMS,
                "model": self.model_name,
                "messages": _messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stop": stop
            }

            for k, v in override_kwargs.items():
                payload[k] = v
                
            url = self.openai_api_base + "/v1/chat/completions"
            
            resp = self.http_session.post(
                url, 
                json=payload
            )

            if resp.status_code == 200:
                return self.commit(InferenceResult(
                    id=self.generate_uuid(),
                    state=InferenceState.DONE,
                    result=resp.json()['choices'][0]['message']['content']
                ))

            logger.error("Failed to get a response from the model. Status code: {}; Text: {}; URL: {}".format(resp.status_code, resp.text, url))

        return self.commit(InferenceResult(
            id=self.generate_uuid(),
            state=InferenceState.ERROR,
            error="Failed to get a response from the model"
        ))

    def __init__(
        self, 
        model_name: str, 
        max_tokens: int,
        model_kwargs: dict, 
        temperature: float,
        max_retries: int, 
        eternal_api_base: str=C.ETERNAL_BACKEND_API, 
        eternal_api_key: str=C.ETERNAL_BACKEND_API_APIKEY,
        eternal_chain_id: str=C.ETERNAL_API_CHAIN_ID
    ):
        super().__init__()

        assert eternal_api_key is not None, "eternalai_api_key is not provided and ETERNAL_BACKEND_API is not set in the environment"
        assert eternal_api_base is not None, "eternalai_api_base is not provided and ETERNAL_BACKEND_API_APIKEY is not set in the environment"
        assert model_name is not None, "model_name is not provided" 

        self.eternal_api_key = eternal_api_key

        self.openai_api_base = eternal_api_base.rstrip("/")
        self.model_name = model_name
        self.model_kwargs = model_kwargs
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.chain_id = eternal_chain_id
        self.http_session = requests.Session()
        self.http_session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.eternal_api_key}"
            }
        )
