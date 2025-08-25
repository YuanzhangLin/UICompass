import time

import re
import subprocess
from configs import *
import Infra.util as util
from Infra.hierarchy import SemanticHierarchy, TotalVisibleHierarchy, VisibleHierarchy
from ExecutionEngine.screen_control import AndroidController
from typing import List, Tuple, Callable
from Infra.infra import TestCase, EventSeq, Event, Widget
from Memory.context import Context, ContextManager
from Agents.agent import Agent

from DomainKnowledgeLoader.error_handler import block_failed_action, restore_state, empty_action_set
from DomainKnowledgeLoader.optimizer import avoid_loop, avoid_repetition, avoid_out_of_app
from DomainKnowledgeLoader.validator import llm_reflection,loop_detection, out_of_app
import client
import llm
import json
from log_util import logger, log_message
import configs
from Infra.history import History

class Guardian:
    target_context: Context
    target: str
    controller: AndroidController
    app: str
    pkg: str
    attempt_cnt: int
    def __init__(self, _app, _pkg, _target: str, _port: str, _generation_limit: int):
        self.app = _app
        self.pkg = _pkg
        configs.package = self.pkg
        self.target = _target
        configs.task = _target.replace(' ', '_').replace("\'", '')
        configs.run_output_path = "./output/" + configs.run_method + "/" + configs.package.replace('.', '_') + '/' + configs.task[:100] + '/'
        configs.run_output_path = configs.run_output_path.replace(':',"").replace("\"","_")
        self.agent = Agent(_app, _target) # LLM agent contains the LLM driver
        self.controller = AndroidController(port=_port) # Android controller is the UI driver
        self.context_manager = ContextManager(_pkg, _app, _target, self.controller) # Context manager is the memory driver
        self.domain_knowledge = {'optimizer':{"avoid_loop":avoid_loop, "avoid_repetition":avoid_repetition,"avoid_out_of_app":avoid_out_of_app}, \
            'validator':{"llm_reflection":llm_reflection, "loop_detection":loop_detection, "out_of_app":out_of_app}, \
            'error_handler':{"block_failed_action":block_failed_action, "restore_state":restore_state, "empty_action_set":empty_action_set}}
        self.attempt_cnt = 0
        self.generation_limit = _generation_limit
        self.instructions = None
        self.step_record = None
        self.activities_sequence = []
        self.instruction_action_times= {} # 记录指令执行次数，用于跳出卡在某个指令。
        self.instruciton_max_try = 3
        self.history = History()
        self.instruction_list = [] # 只用于做实验
        self.instruction_index = 0
        self.history_instructions = [] 

    def add_step(self, activities_sequence, activity_name, step):
        """
        在 activities_sequence 中添加一个步骤：
        - 如果最后一个活动的名称与 activity_name 一致，则将 step 添加到其 steps 中。
        - 否则，创建一个新的活动，并将 step 作为其第一个步骤。
        
        :param activities_sequence: 当前的活动序列（list）
        :param activity_name: 活动的名称（str）
        :param step: 要添加的步骤（str）
        """
        if activities_sequence and activities_sequence[-1]["activity"] == activity_name:
            # 如果最后一个活动是指定的活动，直接添加到其 steps
            activities_sequence[-1]["steps"].append(step)
        else:
            # 如果最后一个活动不是指定的活动，创建新的活动
            activities_sequence.append({
                "activity": activity_name,
                "steps": [step]
            })


    def mainLoop(self) -> EventSeq:
        
        self.context_manager.init_context()

        while self.attempt_cnt < self.generation_limit:
            log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', "This is a event:" + str(self.controller.event_index))

            print('-----------------self.context_manager.get_current_events()------------------')
            for event in self.context_manager.get_current_events():
                print(event)
            print('------------------------over----------------------')

            events = self.domain_knowledge['error_handler']['empty_action_set'](self.context_manager.get_current_events(), self.context_manager)
            current_all_elements = self.context_manager.get_all_elements_string()

            if run_method == code_aware_method:

                if not self.instructions:
                    if configs.uimanual:
                        self.instructions = self.query_instructions_by_codemap(self.target)
                        for activity_instruction in self.instructions['activities_sequence']:
                            for step in activity_instruction['steps']:
                                self.instruction_list.append(step) # 只用于做实验
                    else:
                        self.instructions = self.query_instructions(self.target)
                        for instruction in self.instructions['event_sequence']:
                            self.instruction_list.append(instruction) # 只用于做实验
                    if not configs.adapting:
                        if 'open' or 'Open' in instruction[0]:
                            self.instruction_list.pop(0)# 移除掉第一个是open 一个app的这种。

                if configs.adapting:
                    self.instructions, next_instruction = self.check_instructions(self.target, current_all_elements, events, instructions=self.instructions, history_actions=self.context_manager.getAllHistory())
                    # 获取已经走过的路径。
                    if not next_instruction or next_instruction == "none":
                        if any(s.lower() in current_all_elements.lower() for s in ['ok', 'yes', 'save']):
                            self.instructions, next_instruction = self.check_instructions(self.target, current_all_elements, events, instructions=self.instructions,history_actions=self.context_manager.getAllHistory(), check_OK_button=True)
                            if not next_instruction or next_instruction == "none":
                                break

                        else:
                            break
                        
            # 根据已有信息判断需要选择的元素。
            # 这里要把信息传入。
            logger.info('----------self.instructions')
            logger.info(self.instructions)
            # self.agent.push_data(self.instructions, self.step_record, self.controller.event_index)

            if configs.adapting and  run_method == code_aware_method:
                self.agent.push_data(next_instruction) # 这是原版
            
            # 下面这部分是消融
            if not configs.adapting:
                if self.instruction_index == len(self.instruction_list):
                    print('----------length--------')
                    return
                self.agent.push_data(self.instruction_list[self.instruction_index])


            self.instruction_index += 1
            event = self.agent.plan(events)  # get the UI event to execute from the LLM agent
            event.act(self.controller)

            self.context_manager.update_history(event)
            time.sleep(1)

            if configs.run_method == configs.guardian_method:
                if self.domain_knowledge['validator']['out_of_app'](self.pkg, self.controller):
                    self.domain_knowledge['optimizer']['avoid_out_of_app'](self.context_manager)
                    util.restart_app(pkg=self.pkg)
                    time.sleep(4)
            
            currentContext = self.context_manager.PreUpdateContext(self.controller)    
            # check loop and repetition
            if self.domain_knowledge['validator']['loop_detection'](self.context_manager,currentContext):
                self.domain_knowledge['optimizer']['avoid_loop'](self.context_manager,currentContext)
            else:
                self.context_manager.PostUpdateContext(currentContext)
            
            
            self.attempt_cnt += 1
            if run_method == code_aware_method:
                self.history_instructions.append(next_instruction)
            print('达到次数：', self.attempt_cnt, '   最大次数：', self.generation_limit)
        return EventSeq(self.context_manager.getCurHistory())

    def genTestCase(self) -> TestCase:
        res = TestCase(self.mainLoop(), [context.hierarchy for context in  self.context_manager.contexts])
        print('**'*50)
        print( [context.hierarchy for context in  self.context_manager.contexts])
        return res

    def query_instructions(self):
        answer = client.get_instructions(self.target)
        print('-------query_instructions:')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------query_instructions------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', answer)
        print(answer)
        answer = llm.parse_json(answer)
        return answer

    def activities_sequence_to_string(self, activities_sequence):
        result = []
        for activity in activities_sequence:
            result.append(f"Activity: {activity['activity']}")
            for step in activity["steps"]:
                result.append(f"  - {step}")
            result.append("")  # 添加空行
        return "\n".join(result).strip()  # 移除最后多余的空行

    def get_last_event(self, activities_sequence):
        """
        获取 activities_sequence 中的最后一个事件。
        
        :param activities_sequence: 当前的活动序列（list）
        :return: 最后一个事件的字符串（如果有）
        """
        if not activities_sequence:  # 如果列表为空
            return None
        
        # 获取最后一个活动
        last_activity = activities_sequence[-1]
        
        # 获取最后一个步骤
        if last_activity["steps"]:
            return last_activity["steps"][-1]
        return None






    def get_current_step(self, activities_sequence, instructions, step_record=None):
        #  获取执行到了哪一步。
        history_description = self.activities_sequence_to_string(activities_sequence)
        # index = 1
        # for event in history_actions[:-1]:  # 切片去掉最后一个元素
        #     history_description += 'index-' + str(index) + ':' + str(event) + '\n'
        #     index += 1

        prompt = f'''
        Based on the previous analysis,here is the instructions:\n
        {instructions}\n
        Here is the history_actions:\n
        {history_description}
        Last time, we believed we were at {step_record}:.  

        Now, we just performed {self.get_last_event(activities_sequence)}.  
        Therefore, we want to know which step of the instructions is about {self.get_last_event(activities_sequence)}.
        Please return in JSON format, such as:  
        '''
        prompt += "\n{ \"step\": 1 }\n"
        prompt += "\nNote that: **Do not output anything except the json format answer.**"
        answer = llm.query_llm(prompt)
        data = llm.parse_json(answer)
        logger.info('---------------------prompt---------------------------------')
        logger.info(prompt)
        logger.info('---------------------data---------------------------------')
        logger.info(data)
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------get_current_step  _prompt------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', prompt)
        log_message(configs.run_output_path +  str(self.controller.event_index) + '.log', '------get_current_step   answer------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', answer)
        # 自校正
        last_step_record = data.get("step")
        if not data.get("step") or step_record and data.get("step") < step_record:
            logger.info ('启动自校正')
            return step_record
        # 记录instruction的执行次数
        if last_step_record in self.instruction_action_times:
            self.instruction_action_times[last_step_record] += 1
        else:   
            self.instruction_action_times[last_step_record] = 1
        # 检查是否超过了最大次数。
        if self.instruction_action_times[last_step_record]  > self.instruciton_max_try:
            log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', "instruction += 1")
            last_step_record += 1        
        
        return last_step_record

    def stop_if_last_step(self, instructions, step_record):
        total_number = 0
        for activity in  instructions["activities_sequence"]:
            for step in activity["steps"]:
                total_number += 1
        logger.info('step_record: ', step_record)
        logger.info('total_number:  ', total_number)
        return step_record == total_number


    def get_instructions_history_prompt(self):
        prompt = "\nHere is the history of executed instructions:\n"
        index = 1 
        for instruction in self.history_instructions:
            prompt += f"index-{index}:\"{instruction}\".\n"
            index +=  1
        return prompt



    def get_current_activity(self):
        # 执行 adb 命令获取当前 FocusedApp
        cmd = "adb shell dumpsys window displays | grep mFocusedApp"
        try:
            output = subprocess.check_output(cmd, shell=True, text=True)
        except subprocess.CalledProcessError:
            return None, None  # 命令执行失败

        # 使用正则表达式匹配包名和 Activity
        pattern = r"mFocusedApp=.*?\{(.+?) u\d+ (.+?)/(.+?) .*?\}"
        match = re.search(pattern, output)
        
        if not match:
            return None, None  # 匹配失败

        pid = match.group(1)  # 进程 ID（可选）
        package_name = match.group(2)  # 包名，如 "com.simplemobiletools.contacts.pro"
        activity_name = match.group(3)  # Activity，如 ".activities.MainActivity"

        return package_name, activity_name

    def get_screen_description(self,events: List[Event]):
        filteredEvents = list(filter(lambda x: x[1].strip() != "a View () to click", [(i, e.dump()) for i, e in enumerate(events)]))
        pattern = r"resource_id\ \"key_pos_"

        # 过滤并生成 elemDesc
        elemDesc = [
            f"index-{i}: {x[1]}" 
            for i, x in enumerate(filteredEvents) 
            if not re.search(pattern, x[1])  # 如果 x[1] 包含匹配模式则跳过
        ]
        description = f"\nCurrently we have {len(elemDesc)} widgets, namely:\n" + '\n'.join(elemDesc)
        return description

    def check_instructions(self, task,current_all_elements,events, instructions, history_actions, check_OK_button=False):
        # 根据当前的界面来判断instrctions是否存在问题，是否需要修改。
        instructions_string = str(instructions)
        history_description = ""
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '------history_actions  _prompt------')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', self.context_manager.getAllHistory())
        # index = 1
        # for event in self.context_manager.getAllHistory():
        #     log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', 'index-' + str(index))
        #     log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', str(event))
        #     log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', self.context_manager.getAllHistory())
        #     history_description += 'index-' + str(index) + ':' + str(event) + '\n'
        #     index += 1
        history_description = self.context_manager.getAllHistoryString()
        package_name, activity_name= self.get_current_activity()
        instruction_history_description = self.get_instructions_history_prompt()

        prompt = f"""
        I currently have a task {task}, and I have a set of instructions for this task, but there may be errors in this set of instructions that need to be adjusted based on the current interface.
        
        # Instrctions:
        {instructions_string}

        """
        prompt += 'Here is the information about the screen we are currently on.\n'
        # prompt += current_all_elements
        prompt += self.get_screen_description(events)

        prompt += "\n\n #History information (You should refer to the historical records to identify which part of the instructions they correspond to, consider the relationship between the current interface and the next step, and then update the instructions accordingly.):{\n"
        prompt += history_description

        prompt += instruction_history_description

        prompt +="}\n**Warning:\n"

        prompt += "You should tell me the updated instructions according this format.**Do not output any instructions regarding checking, review or verification, because you are an assistant and cannot perform such operations.**.(**Do not output any else except the json format.**)\n"

        prompt += """
Note that: 
+ current state: Describes the screen status and task status.

+ error reason: When executed correctly, the error reason and revised method should be output as empty. 

+ next_instruction: next_instruction can only contain one instruction. Please note that each instruction should correspond to only one action. If not, please split the instructions, ensuring that each instruction corresponds to a single action.


**If the form has been completed or a pop-up appears on the interface, confirmation may be required at this point. Please check if confirmation terms (such as OK/YES/NO/Cancel) appear on the interface. Consider whether it is necessary to add instructions regarding confirming the form or pop-up.**

We will open the app, so you don't need to open any app.

        """
        repeat = False
        for instruciton in self.history_instructions[:-1]:
            if self.history_instructions[-1] == instruciton:
                prompt += f"\nIt seems that {self.history_instructions[-1]} has already been executed. Please do not repeat the action. If the task is already completed, it should be stopped immediately.\n"

        prompt += f"\nCurrent we are in {activity_name}.Check if any instructions need to be skipped.\n"

        if check_OK_button and any(s.lower() in current_all_elements.lower() for s in ['ok', 'yes']):
            prompt += "\n**It appears that the 'OK' or 'Yes'or 'Save' button was not clicked. Please confirm whether you intend to click the 'OK' or 'Yes' or 'Save' button.**\n"


        # Json格式限制

        prompt += """
Note that:
Return a strictly compliant JSON response with:  
1. **Format Rules**:  
   - Keys and strings must use `"`, never `'`.  
   - No trailing commas (e.g., `{"key": "value"}` ✅, `{"key": "value",}` ❌).  
   - Ensure all `{}` and `[]` are balanced.  
2. **Validation**: The output must pass `JSON.parse()` without errors. 
Validation Instructions:

Before outputting, self-check using JSON.parse() to ensure there are no syntax errors.

You should obey the follew output format. 

# Output Example:
"""

        # 这里为了做实验，最前面强行加了一条打开应用 OK/YES/NO/Cancel
        prompt += '''{
        "task": "Book a flight",
        "explanation": {
            "current state": "The booking is complete but not confirmed",
            "finished step": "All booking steps are done",
            "error reason": "Missing confirmation click on 'Confirm' or 'Book Now' button",
            "revised method": "add confirmation step",
            "next_instruction": "Click 'Confirm' to finalize the booking"
        },
        "updated_activities_sequence": [
            {
                "activity": "LoginActivity",
                "steps": [
                    "1. Open the application Booking"
                    "2. Input the account.",
                    "3. Submit the login form."
                ]
            },
            {
                "activity": "MainActivity",
                "steps": [
                    "4. Search for available flights based on your preferences.",
                    "5. Select the flight that suits your needs."
                ]
            },
            {
                "activity": "BookingActivity",
                "steps": [
                    "6. Enter the required passenger details for booking.",
                    "7. Make the payment for the selected flight.",
                    "8. Receive a confirmation of the flight booking."
                    "9. Click 'OK' to confirm login"  

                ]
            }
        ]
            
        }
        '''
        prompt += "If Task is finished, next_instruction = none"
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '--------check_instructions------prompt')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', prompt)
        answer = llm.query_llm(prompt,  role="You are a user of the app", if_json=True)
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '--------check_instructions------answer')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', answer)

        data = llm.parse_json(answer)

        next_instruction = data['explanation']['next_instruction']
        # 删除'explanation'键
        if 'explanation' in data:
            del data['explanation']

        # 重命名'updated_activities_sequence'键为'activities_sequence'
        if 'updated_activities_sequence' in data:
            data['activities_sequence'] = data.pop('updated_activities_sequence')
        return data, next_instruction


    def load_txt_file(self, file_path):
        """
        加载并读取txt文件内容
        
        参数:
            file_path (str): txt文件的路径
            
        返回:
            str: 文件内容字符串
            或 None (如果读取失败)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except FileNotFoundError:
            print(f"错误：文件 {file_path} 未找到")
            return None
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return None
        
    def construct_prompt_wtg(self, target_task, wtg_file_path):
        prompt = f"I have a task, and the target task is '{target_task}'.\n"

        prompt += "\n Here is the widget transfer graph of the app: \n"
        # load the WTG
        wtg = self.load_txt_file(wtg_file_path)
        prompt += wtg
        prompt += "\nExample:\n"
        prompt += "Output:\n"
        prompt += '''{
        "task": "Book a flight",
        "activities_sequence": [
            {
                "activity": "LoginActivity",
                "steps": [
                    "1. Input the account.",
                    "2. Submit the login form."
                ]
            },
            {
                "activity": "MainActivity",
                "steps": [
                    "3. Search for available flights based on your preferences.",
                    "4. Select the flight that suits your needs."
                ]
            },
            {
                "activity": "BookingActivity",
                "steps": [
                    "5. Enter the required passenger details for booking.",
                    "6. Make the payment for the selected flight.",
                    "7. Receive a confirmation of the flight booking."
                ]
            }
        ],
        "explanation": 
            "because the BookingActivity has the flight booking button."
            
        }
        '''

            
        # Now, ask for the sequence and instructions based on the target task
        prompt += f"\nNote that : **Now I am a user of the app.**.**Output the action can be done by a user.** I want to execute the task '{target_task}', please tell me the sequence of activities the task will go through and provide the instructions.\n"
        prompt += "Output according at the json format.**Do not output anything except the json format answer.**"

        return prompt

    def query_instructions(self, task):

        prompt ="""
        You are a user of an application. Your task is to speculate on what instructions is used to execute the given task.

        """

        prompt += f"""
            Based on the aforementioned application information, our goal is to execute the task: "{task}".
            Please output According at this format,**Do not output any instructions regarding checking, review or verification, because you are an assistant and cannot perform such operations.** **Do not output anyelse except the json format.**
            """
        prompt += "Output:\n"
        prompt += '''{
        "event_sequence": [
                    "1. Open the application Booking ",
                    "2. Input the account.",
                    "3. Submit the login form."
                    "4. Search for available flights based on your preferences.",
                    "5. Select the flight that suits your needs."
                    "6. Enter the required passenger details for booking.",
                    "7. Make the payment for the selected flight.",
                    "8. Receive a confirmation of the flight booking."
        ]
        '''
        
        answer = llm.query_llm(prompt=prompt, role="You are a user of a app")
        instrucions = llm.parse_json(answer)
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '--------query_instructions_by_codemap------prompt')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', prompt)
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', '--------query_instructions_by_codemap------answer')
        log_message(configs.run_output_path  + str(self.controller.event_index) + '.log', answer)
        return instrucions



    def query_instructions_by_codemap(self, task):


        instructions =  client.get_instructions(self.target)
        print(instructions)
        return instructions

