import json
import configs # 在主程序块中，我们会模拟这个导入

# --- (所有类定义保持不变) ---
class Element:
    def __init__(self, name, static_properties, dynamic_properties, dynamic_property):
        self.name = name
        self.static_properties = static_properties
        self.dynamic_properties_list = dynamic_properties
        self.dynamic_property_obj = dynamic_property

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data.get("name", ""),
            static_properties=data.get("static_properties", {}),
            dynamic_properties=data.get("dynamic_properties", []),
            dynamic_property=data.get("dynamic_property", {})
        )

class Layout:
    def __init__(self, name, layout_type, elements, dependencies):
        self.name = name
        self.type = layout_type
        self.elements = elements
        self.dependencies = dependencies

    @classmethod
    def from_dict(cls, data: dict):
        elements = [Element.from_dict(elem_data) for elem_data in data.get("elements", [])]
        dependencies = data.get("dependencies", [])
        return cls(
            name=data.get("name", ""),
            layout_type=data.get("type", ""),
            elements=elements,
            dependencies=dependencies
        )

class Dialog:
    def __init__(self, name, layouts, elements):
        self.name = name
        self.layouts = layouts
        self.elements = elements

    @classmethod
    def from_dict(cls, data: dict):
        layouts = [Layout.from_dict(layout_data) for layout_data in data.get("layouts", [])]
        elements = [Element.from_dict(elem_data) for elem_data in data.get("elements", [])]
        return cls(
            name=data.get("name", ""),
            layouts=layouts,
            elements=elements
        )

class Fragment:
    def __init__(self, name, layouts, dialogs, elements):
        self.name = name
        self.layouts = layouts
        self.dialogs = dialogs
        self.elements = elements

    @classmethod
    def from_dict(cls, data: dict):
        layouts = [Layout.from_dict(layout_data) for layout_data in data.get("layouts", [])]
        dialogs = [Dialog.from_dict(dialog_data) for dialog_data in data.get("dialogs", [])]
        elements = [Element.from_dict(elem_data) for elem_data in data.get("elements", [])]
        return cls(
            name=data.get("name", ""),
            layouts=layouts,
            dialogs=dialogs,
            elements=elements
        )

class Activity:
    def __init__(self, name, layouts, fragments, dialogs, elements, summary, transfer, is_launcher=False):
        self.name = name
        self.layouts = layouts
        self.fragments = fragments
        self.dialogs = dialogs
        self.elements = elements
        self.summary = summary
        self.transfer = transfer
        self.is_launcher = is_launcher  # 新增的属性


    @classmethod
    def from_dict(cls, data: dict):
        layouts = [Layout.from_dict(layout_data) for layout_data in data.get("layouts", [])]
        fragments = [Fragment.from_dict(frag_data) for frag_data in data.get("fragments", [])]
        dialogs = [Dialog.from_dict(dialog_data) for dialog_data in data.get("dialogs", [])]
        elements = [Element.from_dict(elem_data) for elem_data in data.get("elements", [])]
        return cls(
            name=data.get("name", ""),
            layouts=layouts,
            fragments=fragments,
            dialogs=dialogs,
            elements=elements,
            summary=data.get("summary", ""),
            transfer=data.get("transfer", []),
            is_launcher=data.get("is_launcher", False) # 从字典中读取，如果不存在则默认为 False

        )

class UIMap:
    def __init__(self, activities, activities_name):
        self.activities = activities
        self.activities_name = activities_name
        self._activity_map = {activity.name: activity for activity in self.activities}

    @classmethod
    def from_json_file(cls, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        activities = [Activity.from_dict(activity_data) for activity_data in data.get("activities", [])]
        return cls(
            activities=activities,
            activities_name=data.get("activities_name", [])
        )

    def get_activities(self) -> list | None:
        if self.activities:
            return self.activities
        return None

    def get_activity(self, name: str) -> Activity | None:
        if name in self._activity_map:
            return self._activity_map[name]
        for activity in self.activities:
            if activity.name.endswith(f'.{name}'):
                return activity
        return None

    def get_elements(self) -> list | None:
        elements = []
        for activity in self.activities:
            for layout in activity.layouts:
                elements.extend(layout.elements)
            for fragment in activity.fragments:
                elements.extend(fragment.elements)
            for dialog in activity.dialogs:
                elements.extend(dialog.elements)
        if elements:
            return elements
        return None

# --- 函数被重构为返回字符串 ---
def generate_ui_manual_string(ui_map: UIMap, focused_activities: set) -> str:
    """
    根据给定的 UIMap 对象，生成一个代表 UI 手册的格式化字符串。
    """
    # 使用一个列表来收集所有行，最后用换行符连接，效率更高
    manual_lines = []

    manual_lines.append("Here is the UI Map of this app:")
    
    manual_lines.append("Activity list:")
    activity_list_str = ", ".join(ui_map.activities_name) + ","
    manual_lines.append(activity_list_str)
    
    manual_lines.append("Information about these activities: ")
    
    for activity in ui_map.activities:
        if len(focused_activities) != 0 and activity not in focused_activities:
            print(f"exclude the activity{activity}")
            continue
        print(f"add the activity {activity}")

        manual_lines.append(" Activity name: ")
        manual_lines.append(activity.name)

        summary = activity.summary if activity.summary else "No summary provided."
        manual_lines.append(f"The summary of {activity.name}: {summary}")

        if activity.transfer:
            transfer_list_str = ", ".join(activity.transfer)
            manual_lines.append(f"This activity can be transferred to other activities: {transfer_list_str}")

        element_global_index = 1
        for layout in activity.layouts:
            for element in layout.elements:
                parts = []
                if 'tag' in element.static_properties:
                    parts.append(f"tag:{element.static_properties['tag']}")
                if 'id' in element.static_properties:
                    parts.append(f"id:{element.static_properties['id']}")
                
                if element.dynamic_property_obj:
                    if 'action' in element.dynamic_property_obj:
                        parts.append(f"action:{element.dynamic_property_obj['action']}")
                    if 'effect' in element.dynamic_property_obj:
                        parts.append(f"effect:{element.dynamic_property_obj['effect']}")
                
                if parts:
                    element_string = ", ".join(parts)
                    manual_lines.append(f"index-{element_global_index}: {element_string}")
                    element_global_index += 1
        
        # 添加一个空行来分隔不同的 Activity 信息
        manual_lines.append("")
    
    # 将列表中的所有行用换行符连接成一个单一的字符串
    return "\n".join(manual_lines)


# --- 主程序入口（测试部分） ---
if __name__ == "__main__":
    # 为了让代码可独立运行，我们在这里直接定义 JSON 文件路径
    # 在您的实际项目中，可以替换回 import configs 和 configs.code_map_path
    json_file_path = configs.code_map_path

    try:
        # 1. 从文件加载数据到 UIMap 对象
        ui_map_instance = UIMap.from_json_file(json_file_path)
        
        # 2. 调用函数生成完整的字符串
        ui_manual_content = generate_ui_manual_string(ui_map_instance)
        
        # 3. 在测试块中，打印生成的字符串以进行验证
        print(ui_manual_content)
        
        # 你现在可以在其他模块中导入 generate_ui_manual_string 并直接使用其返回的字符串
        # 例如： some_other_module.process(ui_manual_content)

    except FileNotFoundError:
        print(f"错误：JSON 文件未找到，请确保 '{json_file_path}' 文件存在。")
        # 为方便测试，可以提示用户创建一个示例文件
        print("请将您的 JSON 数据保存为 'your_data.json' 文件后再运行。")
    except Exception as e:
        print(f"处理文件时发生错误: {e}")