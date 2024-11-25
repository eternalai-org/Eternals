import queue
from .models import AgentLog, ChainState, ClassRegistration, ChatSession
import threading
import time 
import logging
import traceback
from . import constant as C
from .registry import get_cls, RegistryCategory 
from typing import Any, Callable, Union, Dict
import schedule
from .characters import CharacterBase, DEFAULT_CHAT_COMPLETION_CHARACTER_BUILDER
from .agents import NonInteractiveAgentBase
from .llm import AsyncChatCompletion
from singleton_decorator import singleton

logger = logging.getLogger(__name__)

@singleton
class AutoServiceProvider(object):
    SCRATCHPAD_LENGTH_LIMIT = 30
    CHAT_SESSION_TIMEOUT = 60 * 60 * 3 # 3 hours

    def __init__(self) -> None:
        self._que = queue.Queue() # a queue of ReactAgentReasoningLog
        self._sleep_time = C.AUTO_SERVICE_SLEEP_TIME
        self._interactive_sessions: Dict[str, ChatSession] = {}
        self._characteristic = None

    def initialize_chat_session(self, cfg: dict) -> str:
        x = ChatSession(messages=[{
            'role': 'system',
            'content': DEFAULT_CHAT_COMPLETION_CHARACTER_BUILDER()(self._characteristic)
        }])
        session_id = x.id
        self._interactive_sessions[session_id] = x
        return session_id

    def deinitialize_chat_session(self, session_id: str) -> None:
        if session_id in self._interactive_sessions:
            del self._interactive_sessions[session_id]

        else:
            raise ValueError(f"Session {session_id} not found")

    def get_chat_session(self, session_id: str) -> ChatSession:
        if session_id not in self._interactive_sessions:
            logger.error(f"Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")
        
        return self._interactive_sessions[session_id]

    def execute_chat_completion(self, session_id: str, message: str) -> str:
        if session_id not in self._interactive_sessions:
            logger.error(f"Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")

        session = self._interactive_sessions[session_id]
        llm: AsyncChatCompletion = get_cls(
            RegistryCategory.LLM, session.llm_cfg.name
        )(**session.llm_cfg.init_params)
        
        session.messages.append({
            'role': 'user',
            'content': message
        })

        messages = session.messages
        if len(messages) > self.SCRATCHPAD_LENGTH_LIMIT:
            messages = [messages[0], *messages[1:][-self.SCRATCHPAD_LENGTH_LIMIT:]]

        receipt = llm(messages)
        result = llm.get(receipt.id)
        assistant_message = result.result

        session.messages.append({
            'role': 'assistant',
            'content': assistant_message
        })
        session.last_execution = time.time()

        return assistant_message

    def start(self):
        self._background_thread = threading.Thread(target=self._run, daemon=True)
        self._background_thread.start()

    def init(self, cfg: dict):
        def get_or_warning(d: dict, key: str, default: Any = None) -> Any:
            if key not in d:
                logger.warning(f"Key {key} not found in the config dict")
                return default if not callable(default) else default()

            return d[key]

        characteristic: dict = get_or_warning(cfg, "characteristic", {})
        assert isinstance(characteristic, dict), "Characteristic must be a dictionary with a system_prompt "\
            "or detailed information about the character"

        self._characteristic = characteristic
        missions = get_or_warning(cfg, "missions", [])

        for mission in missions:
            task: str = get_or_warning(mission, "task", "")
            system_reminder: str = get_or_warning(mission, "system_reminder", "")
            toolset_cfg: dict = get_or_warning(mission, "toolset_cfg", {})
            llm_cfg: dict = get_or_warning(mission, "llm_cfg", {})
            agent_builder_cfg: dict = get_or_warning(mission, "agent_builder", {})

            interval_minutes = int(get_or_warning(mission.get("scheduling"), "interval_minutes", None)) 
            
            # build the characteristic of the agent
            character_builder_cfg = ClassRegistration(**get_or_warning(mission, "character_builder", {}))
            character_builder: CharacterBase = get_cls(RegistryCategory.CharacterBuilder, character_builder_cfg.name)()
            system_prompt = character_builder(characteristic_dict=characteristic)

            if interval_minutes is not None and interval_minutes > 0:
                logger.info("Scheduling a mission with interval %d minutes", interval_minutes)

                creator = lambda: AgentLog(
                    system_prompt=system_prompt,
                    task=task,
                    system_reminder=system_reminder,
                    toolset_cfg=[ClassRegistration(**e) for e in toolset_cfg],
                    llm_cfg=ClassRegistration(**llm_cfg),
                    agent_builder=ClassRegistration(**agent_builder_cfg),
                )

                if C.IS_SANDBOX:
                    self.enqueue(creator)

                schedule.every(interval=interval_minutes).minutes.do(self.enqueue, creator)

    def enqueue(self, state: Union[AgentLog, Callable]) -> AgentLog:
        if callable(state):
            state = state()
        
        logger.info("Enqueueing a new state")
        self._que.put(state)
        return state

    def _step(self, log: AgentLog) -> AgentLog:
        agent = get_cls(RegistryCategory.NonInteractiveAgent, log.agent_builder.name)
        
        try:
            agent: NonInteractiveAgentBase = agent(log)
            log = agent(log)
        except Exception as err:
            logger.error(f"Error while executing the agent: {err}")
            log.state = ChainState.ERROR
            log.system_message = str(err)
            
        return log

    def _run(self):
        logger.info("The service is running asynchronously in background")
        
        while True:            
            que_length = self._que.qsize()
            
            if que_length > 0:
                logger.info("Processing %d items in the queue", que_length)

            while not self._que.empty():
                state: AgentLog = self._que.get()

                try:
                    new_state: AgentLog = self._step(log=state)
                except Exception as err:
                    traceback.print_exc()
                    data = state.clone()

                    data.update(
                        state=ChainState.ERROR,
                        system_message=str(err)
                    )

                    new_state = AgentLog(**data)

                if new_state.is_done() or new_state.is_error():
                    continue

                self._que.put(new_state)
                
            to_be_removed_sessions = []

            for session_id, session in self._interactive_sessions.items():
                if time.time() - session.last_execution > self.CHAT_SESSION_TIMEOUT:
                    to_be_removed_sessions.append(session_id)

            for session_id in to_be_removed_sessions:
                logger.info(f"Removing chat session {session_id}")
                del self._interactive_sessions[session_id]

            time.sleep(self._sleep_time)