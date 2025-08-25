# client.py
import requests
import os
import json
# 我们的源码分析 Flask 服务运行在 http://127.0.0.1:5000/
import configs
import prompt
from UIMap import UIMap,generate_ui_manual_string
import llm
import collections

"""
基本上调用code的部分我都是通过这里来调用的。
"""
    
def get_shortest_path(ui_map: UIMap, target_activity_name: str) -> list[str]:
    """
    根据给定的目标活动和 config.main_activity (APP的入口活动)，找到从入口活动到目标活动的最短路径。

    Args:
        ui_map (UIMap): 包含应用所有活动信息的UIMap实例。
        target_activity_name (str): 目标活动的名称（可以是全名或短名称）。

    Returns:
        list[str]: 一个由活动名称构成的列表，表示最短路径。
                   如果不存在路径，则直接返回一个仅包含目标活动名称的列表。
    """
    main_activity_name = configs.main_activity

    # 使用 get_activity 获取规范的活动对象和名称，处理短名称的情况
    start_node = ui_map.get_activity(main_activity_name)
    target_node = ui_map.get_activity(target_activity_name)

    # 1. 边缘情况检查：如果起点或终点活动在UIMap中不存在，则无法找到路径
    if not start_node or not target_node:
        # 即使目标不存在，也按要求返回其名称
        return [target_activity_name]

    start_name = start_node.name
    target_name = target_node.name

    # 2. 如果起点和终点是同一个活动
    if start_name == target_name:
        return [start_name]

    # 3. 使用广度优先搜索 (BFS) 查找最短路径
    # 队列中存储的是到达当前节点的路径（一个活动名称列表）
    queue = collections.deque([[start_name]])
    # visited集合用于存储已访问过的活动名称，防止循环和重复搜索
    visited = {start_name}

    while queue:
        # 取出当前路径
        current_path = queue.popleft()
        # 获取路径的最后一个节点，即当前所在的活动
        current_activity_name = current_path[-1]

        # 如果当前活动就是目标活动，我们找到了最短路径
        if current_activity_name == target_name:
            return current_path

        # 获取当前活动的Activity对象，以查找其可跳转的邻居
        current_activity_obj = ui_map.get_activity(current_activity_name)
        if not current_activity_obj:
            # 如果映射不一致（理论上不应发生），则跳过
            continue

        # 遍历所有可跳转的邻居活动
        for neighbor_name in current_activity_obj.transfer:
            # 如果邻居活动尚未被访问过
            if neighbor_name not in visited:
                # 标记为已访问
                visited.add(neighbor_name)
                # 创建新的路径
                new_path = current_path + [neighbor_name]
                # 将新路径加入队列
                queue.append(new_path)

    # 4. 如果队列为空仍未找到目标，说明从起点无法到达终点
    return [target_activity_name]



def select_focused_activities(ui_map, target_task):
    """
    根据目标任务选择相关的活动。
    
    :param ui_map: UI Map对象
    :param target_task: 目标任务名称
    :return: 相关活动列表
    """
    focused_activities = set()
    prompt_string = prompt.get_focused_activities_prompt(ui_map, target_task)
    response = llm.query_llm(prompt=prompt_string,messages= None, 
    role="You are a helpful AI mobile phone operating assistant.")
    response = llm.parse_json(response)
    important_activity_indexes = response['important_activities']
    for idx, activity in enumerate(ui_map.activities):
        if idx in important_activity_indexes:
            focused_activities.add(activity)
    for activity in focused_activities:
        path = get_shortest_path(ui_map=ui_map, target_activity_name=activity)
        focused_activities.update(path)
    return focused_activities



def get_instructions(target_task):
    ui_map = UIMap.from_json_file(configs.ui_map_path)
    # 如果 Size > config.max_codemap_size, 则需要使用Focusing strategy.
    focused_activities = set()
    if len(ui_map.activities) > configs.max_codemap_size:
        print("UI Map size exceeds the maximum limit, applying Focusing strategy.") 
        focused_activities = select_focused_activities(ui_map=ui_map, target_task=target_task)
    ui_map_string = generate_ui_manual_string(ui_map=ui_map, focused_activities = focused_activities)
    prompt_string = prompt.path_planning_prompt(target_task, ui_map_string)
    response = llm.query_llm(prompt=prompt_string,messages= None, 
    role="You are a helpful AI mobile phone operating assistant.")
    response =  llm.parse_json(response)
    print("Response from LLM:")
    print(response)
    print("Response type:", type(response))
    return response


def get_element_description(element_id):
    ui_map = UIMap.from_json_file(configs.ui_map_path)
    # 获取元素描述
    elements = ui_map.get_elements()
    
    for element in elements:
        if element_id in element.static_properties.get('id', ''):
            description = element.dynamic_property_obj.get('description', '').get('action', '')  + element.dynamic_property_obj.get('description', '').get('effect', '')
            if description:
                return description
            else:
                return f"No description found for element with ID: {element_id}"
    # 如果没有找到对应的元素或描述
    return ""


if __name__ == '__main__':
    # target_task = "Turn on the \"Navigation menu on exit\" setting switch."
    target_task = "disable autosave notes"
    # print(get_instructions(target_task))
    print(get_element_description('save_note'))
    