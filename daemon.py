import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import eternal_agent
import sys
import schedule
import time
from argparse import ArgumentParser

import eternal_agent.utils
import os
import json
from eternal_agent.registry import get_registered, RegistryCategory

def parse():
    parser = ArgumentParser()
    parser.add_argument("-c", "--agent-config-file", type=str, 
                        default=os.path.join(eternal_agent.utils.get_script_dir(__file__), "configs/eternal.json"))
    return parser.parse_args()

def main():
    for item in [RegistryCategory.LLM, RegistryCategory.ToolSet]:
        logger.info(f"Registered {item}: {get_registered(item)}")
    
    service = eternal_agent.service.AutoServiceProvider()
    args = parse()
    assert os.path.exists(args.agent_config_file), f"Config file {args.agent_config_file} not found"
    
    with open(args.agent_config_file, "rb") as f:
        cfg = json.loads(f.read())

    service.schedule(cfg)    
    service.start()

    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logger.error(f"Scheduling error: {e}")
        finally:
            time.sleep(1)

if __name__ == '__main__':
    sys.exit(main())