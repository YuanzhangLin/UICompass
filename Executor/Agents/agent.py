import ExecutionEngine.chatgpt as chatgpt
from configs import *
import Infra.util as util
from Infra.hierarchy import SemanticHierarchy, TotalVisibleHierarchy, VisibleHierarchy
from ExecutionEngine.screen_control import AndroidController
from typing import List, Tuple, Callable
from Infra.infra import TestCase, EventSeq, Event, Widget
from Memory.context import Context
import re
from log_util import logger, important_logger, log_message
import configs
class Agent:
    """
    Represents an LLM agent for Android UI testing.
    Attributes:
    - app (str): The name of the app under test.
    - target (str): The testing objective.
    - initial_prompt (str): The initial prompt for the conversation with the LLM.
    - first_prompt (str): The first prompt for the conversation with the LLM, including the app name and testing target.
    - targetPrompt (str): The prompt reminding the LLM of the testing objective.
    - session (chatgpt.Session): The chatGPT session for the conversation with the LLM.
    Methods:
    - __init__(self, _app, _pkg, _target: str): Initializes the Agent object.
    - act(self, events: List[Event]): Performs an action based on the given events.
    - obtain_event_to_execute(self, events: List[Event]): Obtains the event to execute based on the given events.
    - getInput(self, target) -> str: Asks chatGPT for the text input.
    """
    
    def __init__(self, _app, _target: str):
        self.app = _app
        self.testing_objective = _target
        self.initial_prompt = "Suppose you are an Android UI testing expert helping me write a UI test case. In our " \
                                "conversation, each round I will provide you with a list of UI elements on the screen, " \
                                "and your task is to select one and only one UI element with its index that is the most likely to reach " \
                                "the test target.\n"
                                
        self.first_prompt = self.initial_prompt + \
                            f"We are testing the {self.app} app . " + \
                            f"Our testing target is to {self.testing_objective}ff."

        self.targetPrompt = f"Remember our test target is to {self.testing_objective} on {self.app}."
        # self.targetPrompt = f"Now we are in introActivty, we must go to mainActivity firstly！"
        chatgpt.setupChatGPT(self.first_prompt)
        self.session = None
        #self.session = chatgpt.Session()
        # self.instructions = None
        # self.step_record = None
        # self.event_id = -1
        self.next_instruction =""

    # def push_data(self, instructions, step_record, event_id = -1):

        # self.instructions = instructions
        # self.step_record = step_record   
        # self.event_id = event_id
    def push_data (self, next_instruction):
        self.next_instruction  = next_instruction



    def plan(self, events: List[Event]):
        event = self.obtain_event_to_execute(events)
        if event.action == "text":
            event.input = self.getInput(self.testing_objective)
        return event
    

    def get_next_instruction(self):
        return self.next_instruction
        # if not self.step_record:
        #     self.step_record = 0
        # index = 0
        # for activity in  self.instructions["activities_sequence"]:
        #     for step in activity["steps"]:
        #         index += 1
        #         if index == self.step_record + 1:
        #             # + " explaination: (" + activity["explanation"][index-1] +")"
        #             return step 

    def obtain_event_to_execute(self,events: List[Event]):
        filteredEvents = list(filter(lambda x: x[1].strip() != "a View () to click", [(i, e.dump()) for i, e in enumerate(events)]))
        # elemDesc = [f"index-{i}: {x[1]}" for i, x in enumerate(filteredEvents)]
        # 定义一个正则表达式模式，匹配类似 "resource_id key_pos_2_7" 这种格式的字符串
        pattern = r"resource_id\ \"key_pos_"

        # 过滤并生成 elemDesc
        elemDesc = [
            f"index-{i}: {x[1]}" 
            for i, x in enumerate(filteredEvents) 
            if not re.search(pattern, x[1])  # 如果 x[1] 包含匹配模式则跳过
        ]
        # print('---------elemDesc--------------')
        # print(elemDesc)
        # print('--------elemDesc---------------')

        event_map = {i:e[0] for i,e in enumerate(filteredEvents)}
        description = f"\nCurrently we have {len(elemDesc)} widgets, namely:\n" + '\n'.join(elemDesc)
        task = self.targetPrompt
        if run_method == code_aware_method:
            # print('self.step_record: ',  self.step_record)
            description += f"\nWe now want to execute this instruction **\"{self.get_next_instruction()}\"**, which is part of {task}\nIf no widget is related to the instruction, you should choose the most relative widget about the task {task}.Note that Yes and OK are synonyms, and NO and cancel are synonyms. These two words are not distinguished in the task."

        prompt = '\n'.join([description, task])
        self.session = chatgpt.Session()
        # if self.step_record:
        log_message(configs.run_output_path  + '0.log','----------------------do event prompt----------------------')
        log_message(configs.run_output_path +  '0.log', prompt)

        logger.info('----------------------do event prompt----------------------')
        logger.info(prompt)
        idx = self.session.queryIndex(prompt, lambda x: x in range(len(events)))
        logger.info('----------------------do event prompt result----------------------')
        logger.info(idx)
        # if self.step_record:
        log_message(configs.run_output_path +  '0.log','----------------------do event prompt result----------------------')
        log_message(configs.run_output_path +  '0.log', idx)

        print(idx)
        if HISTORY == HistoryConf.ALL:
            historyDesc = [f"- {e.dump()}" for e in self.getAllHistory()]
            history = f"The user has performed {len(historyDesc)} actions:\n" + '\n'.join(historyDesc)
            description += '\n\n' + history
        elif HISTORY == HistoryConf.PROCESSED:
            historyDesc = [f"- {e.dump()}" for e in self.getCurHistory()]
            history = f"The user has performed {len(historyDesc)} actions:\n" + '\n'.join(historyDesc)
            description += '\n\n' + history
        if idx == -1:
            return Event.back()
        return  events[event_map[idx]]
        

    def getInput(self, target) -> str:
        # ask chatGPT what text to input
        task = "You have selected a TextEdit view, which requires a text input." \
               f"Remember that your task is to {target}"
        requirement = "Please insert the text that you want to input." \
                      "Please only respond with the text input and nothing else."
        if configs.run_method == configs.code_aware_method:
            next = f"Current instruction we want to execute: \"{self.next_instruction}\""
            result = self.session.queryString(f"{task}\n{next}\n{requirement}")

        else:
            # fowller original settings

            result = self.session.queryString(f"{task}\n{requirement}")

        log_message(configs.run_output_path  + '0.log','----------------------getInput----------------------')
        log_message(configs.run_output_path +  '0.log', f"{task}\n{requirement}")
        log_message(configs.run_output_path  + '0.log','----------------------getInput----------------------')
        log_message(configs.run_output_path +  '0.log', result)
        return result



