import json

class CodeMap:
    def __init__(self, activities=None, activities_name=None):
        # 初始化属性
        self.activities = activities if activities is not None else []
        self.activities_name = activities_name if activities_name is not None else []        


    def add_activity(self, activity_name):
        self.activities_name.append(activity_name.rsplit('.',1)[1])
        activity = Activity(activity_name)
        self.activities.append(activity)
        return activity

    def get_activity(self, activity_name):
        for activity in self.activities:
            if activity.name == activity_name or activity_name == activity.name.rsplit('.',1)[1]:
                return activity

    def get_activities(self):
        return self.activities


    @classmethod
    def from_dict(cls, data: dict):
        # 处理 activities 的特殊转换
        activities = [Activity(activity['name']) for activity in data.get('activities', [])]
        # 创建 CodeMap 实例
        return cls(
            activities=activities,
            activities_name=data.get('activities_name', [])
        )

    def to_json(self):
        # 将 CodeMap 类转换为字典格式
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)


class Dialog:
    def __init__(self, name):
        self.name = name
        self.layouts = []
        self.elements = []

    def add_layout(self, layout_name):
        layout = Layout(layout_name)
        self.layouts.append(layout)
        return layout

    def add_element(self, element):
        self.elements.append(element)



class Fragment:
    def __init__(self, name):
        self.name = name
        self.layouts = []
        self.dialogs = []
        self.elements = []

    def add_layout(self, layout_name):
        layout = Layout(layout_name)
        self.layouts.append(layout)
        return layout

    def add_dialog(self, dialog:Dialog)-> Dialog:
        self.dialogs.append(dialog)
        return dialog

    def add_element(self, element):
        self.elements.append(element)

class Layout:
    def __init__(self):
        self.name = ""
        self.elements = []
        self.type = ""
        self.dependencies = []

    def add_element(self, element):
        self.elements.append(element)

    def set_type(self,type):
        self.type = type
    
    def add_dependency(self, layout_dependency):
        self.dependencies.append(layout_dependency)  # 将一个 Layout 对象添加到依赖列表中        

    def to_json(self):
        # 将 CodeMap 类转换为字典格式
        return json.dumps(self, default=lambda o: o.__dict__, indent=4)
    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "elements": [element.to_dict() for element in self.elements],  # 转换所有元素
            "dependencies": [dependency.to_dict() if hasattr(dependency, 'to_dict') else str(dependency) for dependency in self.dependencies],  # 转换依赖
        }

class Element:
    def __init__(self, static_properties=None, dynamic_properties=None):
        self.name = ""
        self.static_properties = static_properties if static_properties else {}
        self.dynamic_properties = dynamic_properties if dynamic_properties else []
    
    def set_name(self, name):
        self.name = name

    def add_static_property(self, key, value):
        self.static_properties[key] = value

    def add_dynamic_property(self, action, effect):
        self.dynamic_properties.append({
            "action": action,
            "effect": effect
        })
    def to_dict(self):
            return {
                "name": self.name,
                "static_properties": self.static_properties,
                "dynamic_properties": self.dynamic_properties
            }

class Activity:
    def __init__(self, name):
        self.name = name
        self.layouts = []
        self.fragments = []
        self.dialogs = []
        self.elements = []
        self.summary = ""
        self.transfer= []


    def add_layout(self, layout:Layout)-> Layout:
        self.layouts.append(layout)
        return layout

    def add_fragment(self, fragment:Fragment)-> Fragment:
        self.fragments.append(fragment)
        return fragment

    def add_dialog(self, dialog:Dialog)-> Dialog:
        self.dialogs.append(dialog)
        return dialog

    def add_element(self, element):
        self.elements.append(element)

    def add_transfer(self, activity_name):
        if activity_name not in self.transfer:
            self.transfer.append(activity_name)


# 示例用法
if __name__ == "__main__":
    code_map = CodeMap()

    # 添加一个 Activity
    activity = code_map.add_activity("MainActivity")

    # 在 Activity 中添加 Layout 和元素
    layout = activity.add_layout("activity_main")
    element = Element("button_submit")
    element.add_static_property("resource-id", "btn_submit")
    element.add_static_property("text", "Submit")
    element.add_dynamic_property("click", "Submit form and go to next page")
    layout.add_element(element)

    # 添加 Fragment 和元素
    fragment = activity.add_fragment("ExampleFragment")
    fragment.add_layout("fragment_example")
    element2 = Element("edit_text_username")
    element2.add_static_property("resource-id", "edit_username")
    element2.add_static_property("hint", "Enter Username")
    element2.add_dynamic_property("input", "User inputs text here")
    fragment.add_element(element2)

    # 添加 Dialog
    activity.add_dialog("AlertDialog")

    # 保存为 JSON
    with open('code_map.json', 'w') as f:
        f.write(code_map.to_json())
