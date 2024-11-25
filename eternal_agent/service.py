import queue
from .models import ReactAgentReasoningLog, ReactChainState, InferenceState, ClassRegistration
from .tools import ToolsetComposer
import threading
import time 
import logging
import traceback
import json
from . import utils
from . import constant as C
from .registry import get_cls, RegistryCategory 
from .llm import AsyncChatCompletion
from typing import Any, Callable, Union, List
import schedule
from .character import build_character

logger = logging.getLogger(__name__)

def build_llm(cfg: ClassRegistration):
    _cls = get_cls(RegistryCategory.LLM, cfg.name)

    if _cls is None:
        logger.error(f"LLM class {cfg.name} not found")
        return None

    return _cls(**cfg.init_params)

def build_toolset(cfg: List[ClassRegistration]) -> ToolsetComposer:
    _cls = [get_cls(RegistryCategory.ToolSet, e.name) for e in cfg]

    for c, n in zip(_cls, cfg):
        if c is None:
            logger.warning(f"Toolset class {n.name} not found")

    _cls = [e for e in _cls if e is not None]

    if len(_cls) == 0:
        logger.error("No toolset class found")
        return None

    _obj = [e(**f.init_params) for e, f in zip(_cls, cfg)]
    return ToolsetComposer(_obj)    

def format_prompt_v2(log: ReactAgentReasoningLog, toolsets: ToolsetComposer):
    template_prompt = '''
You have access to the following toolset:

{tools}

Your reply to user's message must be a single JSON object with exact three keys described as follows.
thought: your own thought about the next step, reflecting your unique persona.
action: must be one of {toolnames}.
action_input: provide the necessary parameters for the chosen action, separating multiple parameters with the | character.

OR with exact two keys as follows.
thought: your final thought to conclude.
final_answer: your conclusion.

{base_system_prompt}

Again, only return a single JSON!
'''

    tool_names = ', '.join(toolsets.names)
    base_tool_str = toolsets.render_instruction()

    system_prompt = template_prompt.format(
        tools=base_tool_str,
        toolnames=tool_names,
        base_system_prompt=log.system_prompt
    )
    
    return system_prompt


def render_conversation(log: ReactAgentReasoningLog, tool: ToolsetComposer):
    system_prompt = format_prompt_v2(log, tool)
    
    conversation = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]
    
    

    for item in log.scratchpad:
        user_message = {}
        for k in ['task', 'observation']:
            if k in item:
                user_message[k] = item[k]

        assistant_message = {}
        for k in ['thought', 'action', 'action_input', 'final_answer']:
            if k in item:
                assistant_message[k] = item[k]

        if len(assistant_message) > 0:
            conversation.append({
                "role": "assistant",
                "content": json.dumps(assistant_message)
            })

        conversation.append({
            "role": "user",
            "content": json.dumps({
                **user_message,
                "system_reminder": log.system_reminder or "Please follow the instructions carefully"
            })
        })

    return conversation

class AutoServiceProvider(object):
    SCRATCHPAD_LENGTH_LIMIT = 30

    def __init__(self) -> None:
        self._que = queue.Queue() # a queue of ReactAgentReasoningLog
        self._sleep_time = C.AUTO_SERVICE_SLEEP_TIME
        
    def start(self):
        self._background_thread = threading.Thread(target=self._run, daemon=True)
        self._background_thread.start()

    def schedule(self, cfg: dict):
        def get_or_warning(d: dict, key: str, default: Any = None) -> Any:
            if key not in d:
                logger.warning(f"Key {key} not found in the config dict")
                return default if not callable(default) else default()

            return d[key]

        characteristic: dict = get_or_warning(cfg, "characteristic", {})
        assert isinstance(characteristic, dict), "Characteristic must be a dictionary with a system_prompt "\
            "or detailed information about the character"

        system_prompt = get_or_warning(characteristic, "system_prompt", lambda: build_character(characteristic))
        missions = get_or_warning(cfg, "missions", [])

        for mission in missions:
            task = get_or_warning(mission, "task", "")
            system_reminder = get_or_warning(mission, "system_reminder", "")
            toolset_cfg = get_or_warning(mission, "toolset_cfg", {})
            llm_cfg = get_or_warning(mission, "llm_cfg", {})
            interval_minutes = int(get_or_warning(mission.get("scheduling"), "interval_minutes", None)) 

            if interval_minutes is not None and interval_minutes > 0:
                logger.info("Scheduling a mission with interval %d minutes", interval_minutes)
                
                if C.IS_SANDBOX:
                    self.enqueue(ReactAgentReasoningLog(
                        system_prompt=system_prompt,
                        task=task,
                        system_reminder=system_reminder,
                        toolset_cfg=[ClassRegistration(**e) for e in toolset_cfg],
                        llm_cfg=ClassRegistration(**llm_cfg)
                    ))
                
                schedule.every(interval=interval_minutes).minutes.do(
                    self.enqueue, 
                    lambda: ReactAgentReasoningLog(
                        system_prompt=system_prompt,
                        task=task,
                        system_reminder=system_reminder,
                        toolset_cfg=[ClassRegistration(**e) for e in toolset_cfg],
                        llm_cfg=ClassRegistration(**llm_cfg)
                    )
                )

    def enqueue(self, state: Union[ReactAgentReasoningLog, Callable]) -> ReactAgentReasoningLog:
        if callable(state):
            state = state()
        
        logger.info("Enqueueing a new state")
        self._que.put(state)
        return state

    def _step(self, log: ReactAgentReasoningLog) -> ReactAgentReasoningLog:
        llm: AsyncChatCompletion = build_llm(log.llm_cfg)
        tool = build_toolset(log.toolset_cfg)
        
        if log.state == ReactChainState.NEW:
            log.state = ReactChainState.RUNNING

            system_prompt = format_prompt_v2(log, tool)
            logger.info("🤖 System: " + system_prompt)
            logger.info("👨‍💻 Task: " + log.task)
            logger.info("🔔 Reminder: " + log.system_reminder)

            log.scratchpad = [
                {
                    "task": log.task.replace('\n', ' ').strip(),
                }
            ]
            receipt = llm(render_conversation(log, tool))
            logger.info("Inference receipt: " + receipt.id)
            log.infer_receipt = receipt.id
            return log

        elif log.state == ReactChainState.RUNNING:
            result = llm.get(log.infer_receipt)
            if result.state == InferenceState.EXECUTING:
                return log
            
            if result.state == InferenceState.ERROR:
                data = log.clone()
                data.update(
                    state=ReactChainState.ERROR,
                    system_message=result.error
                )
                return ReactAgentReasoningLog(**data)
            
            # update the scratch pad
            result = result.result
            pad: dict = utils.parse_conversational_react_response(result)

            if len(pad) == 0:
                data = log.clone()
                data.update(
                    state=ReactChainState.ERROR,
                    system_message="Invalid response from the agent message; Last message: {}".format(result)
                )
                return ReactAgentReasoningLog(**data)

            if 'thought' in pad:
                if 'thought' in log.scratchpad[-1] and any(
                    k not in log.scratchpad[-1] 
                    for k in ['action', 'action_input', 'observation']
                ):
                    for kk in ['action', 'action_input', 'observation']:
                        if kk not in log.scratchpad[-1]:
                            log.scratchpad[-1][kk] = "Not found!"

                    data = log.clone()
                    data.update(
                        state=ReactChainState.ERROR,
                        system_message="Thought found without action/action input/observation"
                    )
                    return ReactAgentReasoningLog(**data)
                else:
                    log.scratchpad.append({
                        "thought": pad['thought']
                    })

            if 'action' in pad:
                if 'action_input' not in pad:
                    log.scratchpad[-1]['action'] = pad['action']
                    log.scratchpad[-1]['action_input'] = "Not found!"
                    
                    data = log.clone()
                    data.update(
                        state=ReactChainState.ERROR,
                        system_message="Action input not found"
                    )
                    
                    return ReactAgentReasoningLog(**data)

                elif 'question' in log.scratchpad[-1]:
                    data = log.clone()
                    data.update(
                        state=ReactChainState.ERROR,
                        system_message="No thought found"
                    )
                    return ReactAgentReasoningLog(**data) 

                action = pad['action']
                action_input = pad['action_input']
                observation = str(tool.execute(action, action_input)) 

                log.scratchpad[-1]['action'] = action
                log.scratchpad[-1]['action_input'] = action_input
                log.scratchpad[-1]['observation'] = observation

                logger.info("🔍 Observation: " + observation)
            if 'final_answer' in pad:
                if any(k in log.scratchpad[-1] for k in ['action', 'action_input', 'observation']):
                    log.scratchpad.append({})
    
                log.scratchpad[-1].update({
                    "final_answer": pad['final_answer']
                })

                log.state = ReactChainState.DONE
                log.system_message = "Final answer found"

                return log

            if len(log.scratchpad) > self.SCRATCHPAD_LENGTH_LIMIT:
                data = log.clone()
                data.update(
                    state=ReactChainState.ERROR,
                    system_message="Scratchpad length exceeded"
                )
                return ReactAgentReasoningLog(**data)

            receipt = llm(render_conversation(log, tool))
            log.infer_receipt = receipt.id 
            return log

        else:
            data = log.clone()
            data.update(
                state=ReactChainState.ERROR,
                system_message="Invalid state {}".format(log.state)
            )
            return ReactAgentReasoningLog(**data)

    def _run(self):
        logger.info("The service is running asynchronously in background")
        
        while True:            
            que_length = self._que.qsize()
            
            if que_length > 0:
                logger.info("Processing %d items in the queue", que_length)

            while not self._que.empty():
                state: ReactAgentReasoningLog = self._que.get()

                try:
                    new_state: ReactAgentReasoningLog = self._step(log=state)
                except Exception as err:
                    traceback.print_exc()
                    data = state.clone()

                    data.update(
                        state=ReactChainState.ERROR,
                        system_message=str(err)
                    )

                    new_state = ReactAgentReasoningLog(**data)

                if new_state.is_done() or new_state.is_error():
                    continue

                self._que.put(new_state)

            time.sleep(self._sleep_time)