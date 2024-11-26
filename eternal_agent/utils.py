import datetime 
import os
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


def build_agent():
    pass

def build_character():
    pass   
