import xml.etree.ElementTree as ET
import json

class AndroidManifestAnalyzer:
    def __init__(self, manifest_path):
        # 加载并解析 AndroidManifest.xml
        self.tree = ET.parse(manifest_path)
        self.root = self.tree.getroot()
        self.activities = {}  # 用于存储活动和它们的迁移关系
        self.init()

    def init(self):
        """
        获取所有的 Activity 信息，返回活动名称的列表。
        """
        activities = []
        for activity in self.root.iter('activity'):
            activity_dict = {}
            for  child in activity:
                activity_dict[child.tag] = child
                # activity_dict[key] = activity.key
            activity_attributes = activity.attrib
            # print(f"Activity: {activity.attrib.get('android:name')}")
            for attr, value in activity_attributes.items():
                activity_dict[attr] = value 
                # if attr == '{http://schemas.android.com/apk/res/android}name':
                    # activity_name = value
                    # print(value)
                # print(f"  {attr}: {value}")
            activity_name = ""
            activity_name = activity_attributes.get('{http://schemas.android.com/apk/res/android}name')
            if not activity_name:
                activity_name = activity.get('{http://schemas.android.com/apk/res/android}name')
            activity_dict["name"] = activity_name
            if activity_name:
                activities.append(activity_dict)
        for activity in activities:
            print(activity.get("name"))
        # 获取别名。
        for activity_alias in self.root.iter('activity-alias'):
            activity_attributes = activity_alias.attrib
            targetActivity = activity_attributes.get('{http://schemas.android.com/apk/res/android}targetActivity')
            is_Main = False
            for intent_filter in activity_alias .iter('intent-filter'):
                for action in intent_filter.iter('action'):
                    if action.get('{http://schemas.android.com/apk/res/android}name') == 'android.intent.action.MAIN':
                        is_Main = True
                        break
            if is_Main:
                for activity in activities:
                    if activity.get('name') == targetActivity:
                        activity['is_main'] = True  
        self.activities = activities
        return activities


    def get_activity_names(self):
        """
        获取所有的 Activity 信息，返回活动名称的列表。
        """
        activity_names = []
        for activity in self.activities:
            activity_names.append(activity.get("name"))
        return activity_names

    def get_full_activity_name(self, package_name):
        activities = self.get_activity_names()
        full_activities = []
        for activity in activities:
            if activity.startswith('.'):
                full_activities.append(package_name + activity)
            else:
                full_activities.append(activity)
        print(full_activities)
        return full_activities


    def get_mainActivity(self):
        """
        获取主 Activity（包含 intent-filter 中 action 为 MAIN 的 Activity）
        """
        # main_activity = None
        # for activity in self.root.iter('activity'):
        #     activity_name = activity.get('{http://schemas.android.com/apk/res/android}name')
        #     # 查找有 intent-filter 且包含 action 为 MAIN 的 activity
        #     for intent_filter in activity.iter('intent-filter'):
        #         for action in intent_filter.iter('action'):
        #             if action.get('{http://schemas.android.com/apk/res/android}name') == 'android.intent.action.MAIN':
        #                 main_activity = activity_name
        #                 break
        #     if main_activity:
        #         break
        for activity in self.activities:
            if activity.get('is_main'):
                return activity.get("name")
        return None
    


    def get_activity_intents(self):
        """
        获取所有活动的 Intent 过滤器，推测活动之间的迁移关系。
        这里我们假设 Intent 是通过目标活动（targetActivity）或其他方式标明迁移关系的。
        """
        migration_graph = {activity: [] for activity in self.get_activities()}

        for activity in self.root.iter('activity'):
            activity_name = activity.get('{http://schemas.android.com/apk/res/android}name')
            if activity_name:
                # 查找该活动的 Intent 过滤器
                for intent_filter in activity.iter('intent-filter'):
                    for action in intent_filter.iter('action'):
                        action_name = action.get('{http://schemas.android.com/apk/res/android}name')
                        if action_name == 'android.intent.action.MAIN':  # 主启动 Activity
                            continue  # 主启动 Activity 一般没有明确的迁移关系
                    # 通过 targetActivity 属性推测迁移关系
                    target_activity = activity.get('{http://schemas.android.com/apk/res/android}targetActivity')
                    if target_activity:
                        migration_graph[activity_name].append(target_activity)

        return migration_graph

    def display_migration_graph(self):
        """
        打印活动之间的迁移图
        """
        migration_graph = self.get_activity_intents()
        print("Activity Migration Graph:")
        for activity, migrations in migration_graph.items():
            print(f"{activity} can migrate to: {', '.join(migrations) if migrations else 'None'}")

    def save_migration_graph(self, output_path):
        """
        将活动迁移图保存为 JSON 格式
        """
        migration_graph = self.get_activity_intents()
        with open(output_path, 'w', encoding='utf-8') as json_file:
            json.dump(migration_graph, json_file, indent=4, ensure_ascii=False)
        print(f"Migration graph saved to {output_path}")


if __name__ == "__main__": 
    # 替换为实际的 AndroidManifest.xml 文件路径
    manifest_path = "D:\code\AndroidSourceCodeAnalyzer/app_project/Omni-Notes/omniNotes/src/main/AndroidManifest.xml"
    
    # 创建分析器对象
    analyzer =  (manifest_path)

    # 获取并打印所有活动
    activities = analyzer.get_activities()
    print("All Activities in the Manifest:")
    for activity in activities:
        print(f"- {activity}")

    # 打印活动迁移关系图
    analyzer.display_migration_graph()

    # 将迁移关系图保存为 JSON 文件
    output_json_path = "./output/migration_graph.json"
    analyzer.save_migration_graph(output_json_path)

