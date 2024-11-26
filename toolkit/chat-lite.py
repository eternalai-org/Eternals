import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

if not load_dotenv():
    logger.warning("Failed to load .env file")

from argparse import ArgumentParser
from eternal_agent import tools, registry, models
import os
import json
import signal

def get_opt():
    parser = ArgumentParser(description="A simple way to chat with your eternal")
    parser.add_argument("-e", "--eternal", type=str, default="configs/eternal.json", help="Host of the daemon")
    parser.add_argument("-f", "--output", type=str, default=None, help="Output file")
    parser.add_argument("-d", "--debug", action="store_true", default=False, help="Debug mode")
    return parser.parse_args()

def main():
    opt = get_opt()
    
    if opt.debug:
        logger.setLevel(logging.DEBUG)
    
    assert os.path.exists(opt.eternal), "Eternal file not found"
    
    with open(opt.eternal, "rb") as f:
        eternal_cfg = json.loads(f.read())
        
    assert "interactive" in eternal_cfg, "Interactive settings (key: interactive) not found in the eternal config file"
    interactive_settings = eternal_cfg["interactive"]

    character_builder_cfg = models.ClassRegistration(**interactive_settings["character_builder"])
    agent_builder_cfg = models.ClassRegistration(**interactive_settings["agent_builder"])
    llm_cfg = models.ClassRegistration(**interactive_settings["llm_cfg"])
    toolsets_cfg = [models.ClassRegistration(**e) for e in interactive_settings["toolset_cfg"]]
    
    print("Loading toolkit...")
    logger.info(
        "\nCharacter builder: %s\nAgent builder: %s\nLLM: %s\nToolsets: %s",
        character_builder_cfg, agent_builder_cfg, llm_cfg, toolsets_cfg
    )
    
    character_builder = registry.get_cls(registry.RegistryCategory.CharacterBuilder, character_builder_cfg.name)(
        **character_builder_cfg.init_params
    )
    
    # agent_builder = registry.get_cls(registry.RegistryCategory.InteractiveAgent, agent_builder_cfg.name)(
    #     **agent_builder_cfg.init_params
    # )
    
    logger.info("Building LLM...")
    _llm = registry.get_cls(registry.RegistryCategory.LLM, llm_cfg.name)(
        **llm_cfg.init_params
    )
    
    toolsets = []
    
    for toolset_cfg in toolsets_cfg:
        toolset = registry.get_cls(registry.RegistryCategory.ToolSet, toolset_cfg.name)(
            **toolset_cfg.init_params
        )
        
        toolsets.append(toolset)

    toolset_composer = tools.ToolsetComposer(toolsets)
    assert "characteristic" in eternal_cfg, "Characteristic (key: characteristic) not found in the eternal config file"

    characteristic = eternal_cfg["characteristic"]
    chat_thread = []

    logger.info("Building agent characteristics...")
    chat_thread.append({
        'role': 'system',
        'content': character_builder(characteristic)
    })
    

    
    # logger.info("Building agent...")
    # agent = agent_builder(characteristic)
    
    MAX_CONVERSATION_LENGTH = 30
    MAX_CONVERSATION_LENGTH += (1 - (MAX_CONVERSATION_LENGTH % 2))
        
    print("Let's chat with your eternal! (Ctrl-C to break)") 
    
    try:
        while True:
            input_message = input("> You: ")

            if len(chat_thread) > MAX_CONVERSATION_LENGTH:
                exceeded = (((len(chat_thread) - MAX_CONVERSATION_LENGTH) + 1) // 2) * 2
                chat_thread = [chat_thread[0], *chat_thread[exceeded:]]

            chat_thread.append({
                'role': 'user',
                'content': input_message
            })

            resp = _llm(chat_thread)
            resp_message = _llm.get(resp.id)

            if resp_message.result is None:
                raise Exception("Failed to get a response from the model")

            chat_thread.append({
                'role': 'assistant',
                'content': resp_message.result
            })

            print(f"> Eternal: {resp_message.result}")
    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, lambda x, y: None)
        
        if opt.output is not None: 
            logger.info("Dumping chat history:")

            with open(opt.output, "w") as f:
                for chat in chat_thread:
                    f.write(f"{chat['role']}: {chat['content']}\n")

            logger.info("Chat history dumped to %s", opt.output)

        print("Exiting chat...")
        
    
if __name__ == '__main__':
    main() 