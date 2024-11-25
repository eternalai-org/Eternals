from .base_agent import NonInteractiveAgentBase
from eternal_agent.models import AgentLog
import logging
from eternal_agent.models import ChainState, InferenceState

logger = logging.getLogger(__name__)

from eternal_agent.registry import get_cls, RegistryCategory, register_decorator
from eternal_agent.models import ClassRegistration, AgentLog     
from typing import List
from eternal_agent.tools import ToolsetComposer
from eternal_agent.llm import AsyncChatCompletion
import json

def format_prompt_v2(log: AgentLog, toolsets: ToolsetComposer):
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


def render_conversation(log: AgentLog, tool: ToolsetComposer):
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

@register_decorator(RegistryCategory.NonInteractiveAgent)
class ReactReasoningAgent(NonInteractiveAgentBase):
    SCRATCHPAD_LENGTH_LIMIT = 30

    def __call__(self, log: AgentLog) -> AgentLog:
        llm: AsyncChatCompletion = build_llm(log.llm_cfg)
        tool = build_toolset(log.toolset_cfg)
        
        if log.state == ChainState.NEW:
            log.state = ChainState.RUNNING

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

        elif log.state == ChainState.RUNNING:
            result = llm.get(log.infer_receipt)
            if result.state == InferenceState.EXECUTING:
                return log
            
            if result.state == InferenceState.ERROR:
                data = log.clone()
                data.update(
                    state=ChainState.ERROR,
                    system_message=result.error
                )
                return AgentLog(**data)
            
            # update the scratch pad
            message_response = result.result
            pad: dict = parse_conversational_react_response(message_response)

            if len(pad) == 0:
                data = log.clone()
                data.update(
                    state=ChainState.ERROR,
                    system_message="Invalid response from the agent message; Last message: {}".format(message_response)
                )
                return AgentLog(**data)

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
                        state=ChainState.ERROR,
                        system_message="Thought found without action/action input/observation"
                    )
                    return AgentLog(**data)
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
                        state=ChainState.ERROR,
                        system_message="Action input not found"
                    )
                    
                    return AgentLog(**data)

                elif 'question' in log.scratchpad[-1]:
                    data = log.clone()
                    data.update(
                        state=ChainState.ERROR,
                        system_message="No thought found"
                    )
                    return AgentLog(**data) 

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

                log.state = ChainState.DONE
                log.system_message = "Final answer found"

                return log

            if len(log.scratchpad) > self.SCRATCHPAD_LENGTH_LIMIT:
                data = log.clone()
                data.update(
                    state=ChainState.ERROR,
                    system_message="Scratchpad length exceeded"
                )
                return AgentLog(**data)

            receipt = llm(render_conversation(log, tool))
            log.infer_receipt = receipt.id 
            return log

        else:
            data = log.clone()
            data.update(
                state=ChainState.ERROR,
                system_message="Invalid state {}".format(log.state)
            )
            return AgentLog(**data)