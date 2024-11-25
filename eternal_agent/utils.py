import datetime 
import os
import json
from typing import Optional
import logging
from .models import InferenceResult
import queue
from singleton_decorator import singleton

logger = logging.getLogger(__name__)

def formated_utc_time():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def get_script_dir(ee = __file__):
    return os.path.dirname(os.path.realpath(ee))

def parse_conversational_react_response(response: str, verbose=True) -> dict:
    try:
        json_response = json.loads(response)
    except json.JSONDecodeError:
        return {}

    segment_pad = {}

    if "thought" in json_response:
        not verbose or logger.info("🤔 Thought: " + json_response["thought"])
        segment_pad.update({
            "thought": json_response["thought"]
        })

    if "final_answer" in json_response:
        segment_pad.update({
            "final_answer": json_response["final_answer"]
        })
        not verbose or logger.info("🎯 Final Answer: " + json_response["final_answer"])

        return segment_pad

    if "action" in json_response:
        segment_pad.update({
            "action": json_response["action"]
        })
        not verbose or logger.info("🛠️ Action: " + json_response["action"])

        if "action_input" not in json_response:
            json_response["action_input"] = ""

    if "action_input" in json_response:
        not verbose or logger.info("📥 Action Input: " + json_response["action_input"])

        segment_pad.update({
            "action_input": json_response["action_input"]
        })

    return segment_pad

@singleton
class SimpleCacheMechanism(object):
    MAX_CACHE_ITEMS = 2048

    def __init__(self, *args, **kwargs):
        self._log = {}
        self._que = queue.Queue()

    def commit(self, result: InferenceResult) -> InferenceResult:
        self._log[result.id] = result
        self._que.put(result.id)

        while len(self._log) > self.MAX_CACHE_ITEMS:
            top = self._que.get()
            self._log.pop(top)

        return result

    def get(self, id: str, default=None) -> Optional[InferenceResult]:
        return self._log.get(id, default)