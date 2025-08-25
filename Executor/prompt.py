from UIMap import UIMap

def path_planning_prompt(target_task: str, ui_map: UIMap):
    """
    生成路径规划的提示信息。
    
    :param target_task: 目标任务名称

    """
    prompt ="""
    [Background]
    I need to execute a target task within the application. Could you assist in defining the step-by-step instructions to achieve it? I will provide you with the UI Map for the application. The UI Map is a graph used to describe the application's user interface and interaction logic. Your task is to speculate on what instructions are used to execute the given task.
    [UI Map]
    """
    prompt += ui_map
    prompt += f"""
    [Task Description]
    Based on the aforementioned application information, our goal is to execute the task: {target_task}.

    [Output Example]
    Here's a reference output example. Based on this format, list all activities involved in the task and corresponding instructions per activity. Output must adhere to the following JSON format.
    """
    prompt += """
    {
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

    **Do not output anyelse except the JSON formar answer.**
    """
    prompt += f"\n[Target Task]\n{target_task}\n"
    return prompt



def get_focused_activities_prompt(ui_map: UIMap, target_task: str):
    """
    根据目标任务选择相关的活动。
    
    :param ui_map: UI Map对象
    :param target_task: 目标任务名称
    :return: 相关活动列表
    """
    prompt = """
      [Background]
      I need to execute a target task within the application. But the size of the UI Map is too large to process.
      Therefore, I need to focus on the activities that are relevant to the target task. Could you assist in selecting the activities that are relevant to the target task? I will provide you with the UI Map for the application. The UI Map is a graph used to describe the application's user interface and interaction logic. Your task is to select the activities that are relevant to the target task.
      [UI Map]
      The list of activities:
      """
    index = 0
    for activity in ui_map.activities:
        prompt += f"Index-{index} Activity name: {activity.name}\n"
        summary = activity.summary if activity.summary else "No summary provided."
        prompt += f"The summary of {activity.name}: {summary}\n"
        index += 1
    prompt += f"""
      [Target task]
      The task is {target_task}
      [Output Example]
      Here's a reference output example. Based on this format, list all important activities involved in the task. Output must adhere to the following JSON format. You just need to output the indexes of activities. For example, if you think index-1, index-2 and index-3 is important for executing, you should output like this.
      Do not output anything except the JSON format output.
    """
    prompt += """
      {
        "important_activities":[1,2,3]
      }
      """
    return prompt
