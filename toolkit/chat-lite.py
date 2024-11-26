import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

if not load_dotenv():
    logger.warning("Failed to load .env file")

from argparse import ArgumentParser
from eternal_agent import registry, models, agents
import os
import sys
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

    logger.info("Loading character builder settings...")
    character_builder_cfg = models.ClassRegistration(**interactive_settings["character_builder"])
    
    logger.info("Loading agent builder settings...")
    agent_builder_cfg = models.ClassRegistration(**interactive_settings["agent_builder"])
    
    logger.info("Loading LLM settings...")
    llm_cfg = models.ClassRegistration(**interactive_settings["llm_cfg"])
    
    logger.info("Loading toolset settings...")
    toolsets_cfg = [
        models.ClassRegistration(**e) 
        for e in interactive_settings["toolset_cfg"]
    ]
    
    logger.info(
        "\n\nCharacter builder: %s\n\nAgent builder: %s\n\nLLM: %s\n\nToolsets: %s",
        character_builder_cfg, agent_builder_cfg, llm_cfg, toolsets_cfg
    )    
    

    assert "characteristic" in eternal_cfg, "Characteristic (key: characteristic) not found in the eternal config file"

    characteristic = models.Characteristic(**eternal_cfg["characteristic"])

    model = models.AgentLog(
        characteristic=characteristic,
        llm_cfg=llm_cfg,
        agent_builder_cfg=agent_builder_cfg,
        character_builder_cfg=character_builder_cfg,
        toolset_cfg=toolsets_cfg
    )
    
    logger.info("Building agent...")
    
    agent: agents.InteractiveAgentBase = registry.get_cls(registry.RegistryCategory.InteractiveAgent, agent_builder_cfg.name)(
        model,
        **agent_builder_cfg.init_params
    )

    chat_thread = []
    
    MAX_CONVERSATION_LENGTH = 30
    MAX_CONVERSATION_LENGTH += (1 - (MAX_CONVERSATION_LENGTH % 2))
        
    print("Let's chat with your eternal! (Ctrl-C to break)") 
    
    try:
        while True:
            # flush the stdin
            sys.stdin.flush()            
            input_message = input("> You: ")
            
            try:
                resp: models.AssistantResponse = agent.step(
                    models.Mission(system_reminder="", task=input_message)
                )

            except Exception as e:
                logger.error("An error occurred: %s", e)
                break 

            print(f"> Eternal: " + resp.content)

            chat_thread.extend([
                {
                    "role": "user",
                    "content": input_message
                }, 
                {
                    "role": "assistant",
                    "content": resp.content
                }
            ])

    except KeyboardInterrupt:
        signal.signal(signal.SIGINT, lambda x, y: None)

    if opt.output is not None: 
        logger.info("Dumping chat history:")

        with open(opt.output, "w") as f:
            for chat in chat_thread:
                f.write(f"{chat['role']}: {chat['content']}\n\n")

        logger.info("Chat history dumped to %s", opt.output)

    print("Exiting chat...")
    
if __name__ == '__main__':
    main() 