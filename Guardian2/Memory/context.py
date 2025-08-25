from Infra.hierarchy import SemanticHierarchy, TotalVisibleHierarchy, VisibleHierarchy, Hierarchy
from typing import List, Tuple, Callable
from Infra.infra import TestCase, EventSeq,  Event, Widget
from configs import *
from ExecutionEngine.screen_control import AndroidController
import Infra.util as util
import ExecutionEngine.chatgpt as chatgpt
import time
import configs
from log_util import logger, important_logger, log_message
import re

class Context:
    '''
    A context is a UI state maintains the following information:
    - activity: the current activity
    - hierarchy: the processed hierarchy of the current activity, containing interactable UI actions used for UI state hashing.
    - bannedEvents: the disabled events based on domain knowledge.
    - event: the selected UI event in this UI state; disallow repeated selection.
    '''
    hierarchy: Hierarchy
    activity: str
    bannedEvents = List[Event]
    target: str

    def __init__(self, activity: str, target: str, hierarchy: Hierarchy):
        self.target = target
        self.hierarchy = hierarchy
        self.activity = activity
        self.event = None
        self.bannedEvents = []
        self.initial_prompt = "Suppose you are an Android UI testing expert helping me write a UI test case. In our " \
                              "conversation, I will provide you with a list of UI elements with texts on the screen, " \
                              "and your task is to select the group of texts that are relevant to the test target.\n" \
                              f"Our testing target is to {self.target} and validate whether the app behaves correctly."

    def setRelevant(self):
        '''
        Filter textual information with rule-based heuristics or LLM-based heuristics.
        '''
        if INFODISTILL == InformationDistillationConf.CHATGPT and configs.run_method == configs.guardian_method:
            self.setTextRelevant()
            self.setContentDescRelevant()
        else:
            for w in self.hierarchy:
                w.contentDescRelevant = True if w.contentDesc.strip() != '' else False
                w.textRelevant = True if w.contentDescRelevant is not True else False

    def setTextRelevant(self):
        texts = list({w.text for w in self.hierarchy if w.text.strip() != ""})
        if len(texts) == 0:
            return

        textMapping = {t: set() for t in texts}
        for idx, w in enumerate(self.hierarchy):
            if w.text.strip() != "":
                textMapping[w.text].add(idx)
        interestingTextConsts = ["OFF", "ON"]
        if any([not util.isInteger(s) and s not in interestingTextConsts for s in texts]):
            interestingTexts = list(filter(lambda s: util.isInteger(s) or s in interestingTextConsts, texts))
            texts = list(filter(lambda s: not util.isInteger(s) and s not in interestingTextConsts, texts))
            elemTexts = [f"{idx}. " + m for idx, m in enumerate(texts)]

            description = f"Currently we have {len(elemTexts)} texts:\n" + '\n'.join(elemTexts)
            task = f"Remember that your task is to {self.target}. "
            prompt = '\n'.join([description, '', task])
            interestingTexts.extend([texts[idx] for idx in chatgpt.Session([('system', self.initial_prompt)]) \
                                    .queryListOfIndex(prompt, lambda x: x < len(texts))])
        else:
            interestingTexts = texts

        for text in interestingTexts:
            for i in textMapping[text]:
                self.hierarchy[i].textRelevant = True

    def setContentDescRelevant(self):
        descMapping = [(w.contentDesc, idx) for idx, w in enumerate(self.hierarchy) if w.contentDesc.strip() != '']
        if len(descMapping) == 0:
            return
        elemDescs = [f"{idx}. " + m[0] for idx, m in enumerate(descMapping)]

        description = f"Currently we have {len(elemDescs)} texts:\n" + '\n'.join(elemDescs)
        task = f"Remember that your task is to {self.target}. "
        prompt = '\n'.join([description, '', task])

        for idx in chatgpt.Session([('system', self.initial_prompt)]).queryListOfIndex(prompt,
                                                                                       lambda x: x < len(descMapping)):
            self.hierarchy[descMapping[idx][1]].contentDescRelevant = True
        for w in self.hierarchy:
            if "ImageButton" in w.clazz:
                w.contentDescRelevant = True

    def setEvent(self, event: Event):
        self.event = event

    def get_elements_as_string(self):
        return self.hierarchy.get_elements_as_string()
    
    # get all available events (remove banned ones)
    def getEvents(self) -> List[Event]:
        if INFODISTILL in [InformationDistillationConf.SCRIPT, InformationDistillationConf.CHATGPT]:
            events = self.hierarchy.getEvents()
            # TODO: add unique
            # return list(filter(lambda x: x not in self.bannedEvents, events))
            # 如果是情况 A，返回过滤后的 events
            if configs.run_method == configs.guardian_method:  # 这里替换成实际的情况A条件
                return list(filter(lambda x: x not in self.bannedEvents, events))
                
            # 如果是情况 B，直接返回原始的 events
            elif configs.run_method == configs.code_aware_method:  # 这里替换成实际的情况B条件
                return events
        raise NotImplementedError()

        # SHUFFLE
        # shuffle(events)

    def __eq__(self, other: "Context"):
        def isVisible(node):
            return all(node.get(p) == "true" for p in ['focusable', 'visible-to-user'])


        if self.activity is not None and other.activity is not None and self.activity != other.activity:
            print(self.activity, other.activity)
            return False

        ui_hash_set = {hash(widget) for widget in self.hierarchy}
        cur_hash_set = {hash(widget) for widget in other.hierarchy}
        #print(ui_hash_set, cur_hash_set)
        #print(list(map(lambda x: x.attrib, self.hierarchy)), list(map(lambda x: x.attrib, other.hierarchy)))
        if len(cur_hash_set & ui_hash_set) / len(cur_hash_set | ui_hash_set) > 0.8:
            return True
        else:
            return False

    def ban(self, event: Event):
        if event != Event.back():
            self.bannedEvents.append(event)

    def ban_current(self):
        self.ban(self.event)
        self.event = None


class ContextManager:
    contexts: List[Context]
    history: List[Context]
    all_contexts: List[Context]
    all_events: List[Event]
    
    def __init__(self, pkg:str, app:str, target: str, controller: AndroidController):
        self.pkg = pkg
        self.app = app
        self.target = target
        self.controller = controller  # 新增controller作为属性
        
        self.all_contexts = []
        self.history = []
        self.contexts = []
        self.all_events = []
        self.last_event = None

    def init_context(self):
        self.contexts = []
        self.history = []
        self.all_contexts = []
        self.all_events = []
        self.last_event = None
        initContext:    Context = self.getCurrentContext(self.controller)
        if len(self.history) == 0:
            self.history.append(initContext)
        self.all_contexts = [initContext]
        self.contexts = [initContext]
        # self.contexts[-1].setRelevant()    

    def getCurHistory(self) -> List[Event]:
        return [context.event for context in self.contexts[:-1]]

    def getAllHistory(self) -> List[Event]:
        
        result = [context.event for context in self.all_contexts[:-1]]
        log_message(configs.run_output_path  + str(len(self.all_events)) + '.log', "-------getAllHistory")
        log_message(configs.run_output_path  + str(len(self.all_events)) + '.log', str(self.all_events))

        return result


    def format_events(self, input_string):
        # 使用正则表达式提取所有 Event 对象
        event_pattern = r"Event\(.*?\)"
        events = re.findall(event_pattern, input_string)

        # 构造带有索引的输出格式
        formatted_events = []
        for index, event in enumerate(events, start=1):
            formatted_events.append(f"index-{index}: {event}")

        return "\n".join(formatted_events)

    def getAllHistoryString(self) -> str:

        index  =1
        description = "index-0: open the target appliaction\n"
                # description  = str(self.getAllHistory())
        # description = self.format_events(description)
        # result = [context.event for context in self.all_contexts[:-1]]
        for event in self.all_events:
        # for contenxt in self.all_contexts[:-1]:
            description += 'index-' + str(index) + ':' + str(event) + '\n'
            index += 1


        return description

    def getCurrentContext(self, controller:AndroidController) -> Context:
        return Context(controller.app_info()[1], self.target,
                       SemanticHierarchy(self.pkg, self.app, controller.device.dump_hierarchy(),
                                         controller.device.dump_hierarchy()))
    def get_current_events(self):
        return self.contexts[-1].getEvents()

    def get_all_elements(self):
        return self.contexts[-1].get_all_elements_with_id()

    def get_all_elements_string(self):
        return self.contexts[-1].get_elements_as_string()

    def update_history(self,event):
        self.last_event = event
        self.all_events.append(event)
        self.contexts[-1].setEvent(event)
        # print('--------------all_events-------------')
        # # print(self.all_events)
        # for event in self.all_events:
        #     print(event)
        log_message(configs.run_output_path  + str(len(self.all_events)) + '.log', 'add----event........')
        log_message(configs.run_output_path  + str(len(self.all_events)) + '.log', str(event))
        log_message(configs.run_output_path  + str(len(self.all_events)) + '.log', str(self.all_events))


        
    def PreUpdateContext(self,controller:AndroidController)->Context:
        currentContext = self.getCurrentContext(controller)
        self.all_contexts.append(currentContext)
        self.history.append(currentContext)
        return currentContext

    def PostUpdateContext(self,currentContext:Context):
        currentContext.setRelevant()
        event: Event = self.contexts[-1].event
        if event and event.action == "text":
            currentContext.ban(event)
        self.contexts.append(currentContext)
    