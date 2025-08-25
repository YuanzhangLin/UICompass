from openai import OpenAI
import json
import time



def query_llm(prompt, messages= None, role="You are a android source code analysis assistant", if_json = False):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # if attempt<3:
                # prompt += "\n\n**Please note that your answer should obey the json format.\" should be use \\\"!**"
            llm_response = query_llm_single(prompt,messages=messages)
            if if_json:
                parsed = parse_json(llm_response)
            return llm_response
        except (json.JSONDecodeError,UnboundLocalError, ValueError) as e:
            if attempt == max_retries - 1:
                raise ValueError(f"Failed to parse JSON after {max_retries} attempts. Last error: {str(e)}")
            continue
    
    # This line should theoretically never be reached
    raise ValueError("Unexpected error in query_llm_single")



def query_llm_single(prompt, messages= None, role="You are a android task agent"):
    # return quert_llm(prompt)
    # return query_deep_seek_huoshan(prompt)
    print('=============prompt=================')
    if prompt:
        print(prompt)
    else:
        print(messages)
    print('----------over---------')
    attempts = 0
    max_attempts = 2
    result = None

    while attempts < max_attempts:
        start_time = time.time()
        result = query_deep_seek_bailian(prompt,message=messages)# , message=messages
        end_time =time.time()
        elapsed_time = end_time - start_time
        print(f"查询耗时：{elapsed_time:.2f} 秒")
        if result:
            break
        attempts += 1

    return result



def query_qwen_max_bailian(prompt, message=None, role="You are a android source code analysis agent"):
    client = OpenAI(
    api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message

    completion = client.chat.completions.create(
        model="qwen-plus",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    return completion.choices[0].message.content


def query_deep_seek(prompt, role="You are a android source code analysis assistant"):
    client = OpenAI(
        api_key = "sk-60d030fc62da44dda74f4425ef797f9b",
        base_url = "https://api.deepseek.com",
    )
    # Streaming:
    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages = [
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
        ],
        stream=False
    )

    return completion.choices[0].message.content


def query_deep_seek_huoshan(prompt, role="You are a android source code analysis assistant"):
    client = OpenAI(
        api_key = "b6db6f23-cd8d-46c2-b27e-cfa58e2f672d",
        base_url = "https://ark.cn-beijing.volces.com/api/v3",
    )

    # Streaming:

    completion = client.chat.completions.create(
        model = "ep-20250207124903-xnshd",  # your model endpoint ID
        messages = [
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
        ],
        stream=False
    )

    return completion.choices[0].message.content


def query_deep_seek_bailian(prompt, message=None, role="You are a android source code analysis assistant"):
    client = OpenAI(
    api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message

    completion = client.chat.completions.create(
        model="deepseek-v3",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    return completion.choices[0].message.content


# 因为别人问我为什么不用其他模型，我就不得不跑一下qwen-7B。-json都生成不准
def query_qwen_bailian(prompt, message=None, role="You are a android source code analysis assistant"):
    client = OpenAI(
    api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message

    completion = client.chat.completions.create(
        model="qwen2.5-7b-instruct-1m",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    return completion.choices[0].message.content


# 因为别人问我为什么不用其他模型，我就不得不跑一下qwen-7B。-json都生成不准
def query_qwen_72B_bailian(prompt, message=None, role="You are a android source code analysis assistant"):
    client = OpenAI(
    api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message

    completion = client.chat.completions.create(
        model="qwen2.5-72b-instruct",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    return completion.choices[0].message.content

def query_qwen_vl_max_bailian(prompt, message=None, role="You are a android task agent"):
    client = OpenAI(
    api_key="sk-ea7aaa1057804b52ba99d14ca39543c0",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message

    completion = client.chat.completions.create(
        model="qwen-vl-max",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    return completion.choices[0].message.content




# openrouter,72B千问
def query_qwen_72B_openrouter(prompt, message=None, role="You are a android source code analysis assistant"):
    client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1",
    )
    if not message:
        messages=[
            {'role': 'system', 'content': role},
            {'role': 'user', 'content': prompt}
            ]
    else:
        messages = message

    completion = client.chat.completions.create(
        extra_headers={
            "HTTP-Referer": "<YOUR_SITE_URL>", # Optional. Site URL for rankings on openrouter.ai.
            "X-Title": "<YOUR_SITE_NAME>", # Optional. Site title for rankings on openrouter.ai.
        },
        extra_body={},
        model="qwen/qwen-2.5-72b-instruct:free",  # 此处以 deepseek-r1-distill-qwen-7b 为例，可按需更换模型名称。
        messages=messages
    )
    return completion.choices[0].message.content

def check_braces(json_string):
   stack = []
   for char in json_string:
       if char == '{':
           stack.append(char)
       elif char == '}':
           if not stack:
               return False  # 找到闭合括号但没有对应的开启括号
           stack.pop()
   
   return len(stack) == 0  # 栈为空表示所有括号都匹配

def parse_json(answer):
    file_path = './temp.json'
    # 将 answer 转换为字符串（确保它是字符串类型）
    answer = str(answer)
    
    print('--------------original answer---------', answer)
    print('---------over-------------')

    # 如果包含 '```json'，则去除代码块标记
    if '```json' in answer:
        answer = answer.replace("```json", "").replace('```', '')    
    answer = answer.strip()

    if not check_braces(answer):
        print('----括号不匹配。')
        if '{"{"' in answer: #第一种情况
            answer = answer.replace('{"{"', '{"')
        elif '{{' in answer:
            answer = answer.replace('{{','{')
        else:
            answer = answer.replace('{', '', 1)


    # 打印清理后的内容
    print('-------清理后的内容-------\n', answer,'\n----------\n')

    # 步骤 1: 将 answer 保存到指定路径的正式文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(answer)
    print(f"Data saved to {file_path}")

    # 步骤 2: 从文件读取数据
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()

    # 打印文件内容（调试用）
    
    # 步骤 3: 解析 JSON 字符串
    try:
        data = json.loads(file_content)  # 解析 JSON 数据
    except json.JSONDecodeError as e:
        # try:
        #     file_content.replace('{\"{\"','{\"')
        #     data = json.loads(file_content)
        # except json.JSONDecodeError as e:

        print('Error parsing JSON:', e)
    return data

if __name__ == '__main__':
    # print(quert_llm('????'))
    test_prompt = """
        I currently have a task change the theme color to white and save it, and I have a set of instructions for this task, but there may be errors in this set of instructions that need to be adjusted based on the current interface.
        
        # Instrctions:
        {'task': 'Change the theme color to white and save it', 'activities_sequence': [{'activity': 'SettingsActivity', 'steps': ['1. Open the SettingsActivity from the main menu or navigation.', "2. Scroll down to the 'Color Customization' section.", "3. Click on the 'Widget Color Customization' label or button.", '4. In the WidgetRecordDisplayConfigureActivity, select the color white using the color picker.', '5. Adjust the transparency seekbar if necessary (set to 100% opacity for solid white).', "6. Click the 'Save' button to apply the changes."]}], 'explanation': 'because the SettingsActivity contains options for color customization, and the WidgetRecordDisplayConfigureActivity allows for detailed color and transparency settings.'}

        Here is the information about the screen we are currently on.
Widget(resource-id: com.simplemobiletools.voicerecorder:id/action_bar_root, class: android.widget.FrameLayout, position: (0, 74, 1080, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/main_coordinator, class: android.view.ViewGroup, position: (0, 74, 1080, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/main_menu, class: android.widget.LinearLayout, position: (0, 74, 1080, 242))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/top_app_bar_layout, class: android.widget.LinearLayout, position: (42, 74, 1038, 242))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/top_toolbar_holder, class: android.widget.RelativeLayout, position: (42, 95, 1038, 221))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/top_toolbar_search_icon, content-desc: Search, class: android.widget.ImageView, position: (42, 95, 147, 221))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/top_toolbar_search, text: Search, class: android.widget.EditText, position: (147, 95, 731, 221))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/top_toolbar, class: android.view.ViewGroup, position: (731, 95, 1027, 221))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/settings, content-desc: Settings, class: android.widget.Button, position: (773, 95, 900, 221))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/about, content-desc: About, class: android.widget.Button, position: (900, 95, 1027, 221))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/main_holder, class: android.widget.RelativeLayout, position: (0, 242, 1080, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/view_pager, class: f4.i, position: (0, 242, 1080, 2109))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_holder, class: android.view.ViewGroup, position: (0, 242, 1080, 2109))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recordings_fastscroller, class: android.widget.RelativeLayout, position: (0, 242, 1080, 1599))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recordings_list, class: androidx.recyclerview.widget.RecyclerView, position: (0, 242, 1080, 1599))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_frame, text: test1.m4a, class: android.widget.FrameLayout, position: (0, 242, 1080, 411))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/item_holder, class: android.view.ViewGroup, position: (0, 242, 1080, 411))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_title, text: test1.m4a, class: android.widget.TextView, position: (42, 274, 840, 329))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_duration, text: 00:06, class: android.widget.TextView, position: (840, 276, 933, 327))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_date, text: 16.01.2025, 01:14 PM, class: android.widget.TextView, position: (42, 329, 809, 380))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_size, text: 75.3 kB, class: android.widget.TextView, position: (809, 329, 933, 380))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/overflow_menu_icon, class: android.widget.ImageView, position: (933, 263, 1080, 390))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_frame, text: test2.m4a, class: android.widget.FrameLayout, position: (0, 416, 1080, 585))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/item_holder, class: android.view.ViewGroup, position: (0, 416, 1080, 585))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_title, text: test2.m4a, class: android.widget.TextView, position: (42, 448, 840, 503))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_duration, text: 00:05, class: android.widget.TextView, position: (840, 450, 933, 501))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_date, text: 16.01.2025, 01:14 PM, class: android.widget.TextView, position: (42, 503, 809, 554))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_size, text: 70.4 kB, class: android.widget.TextView, position: (809, 503, 933, 554))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/overflow_menu_icon, class: android.widget.ImageView, position: (933, 437, 1080, 564))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_frame, text: Test3.mp3, class: android.widget.FrameLayout, position: (0, 590, 1080, 759))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/item_holder, class: android.view.ViewGroup, position: (0, 590, 1080, 759))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_title, text: Test3.mp3, class: android.widget.TextView, position: (42, 622, 840, 677))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_duration, text: 01:49, class: android.widget.TextView, position: (840, 624, 933, 675))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_date, text: 16.01.2025, 01:14 PM, class: android.widget.TextView, position: (42, 677, 817, 728))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_size, text: 1.3 MB, class: android.widget.TextView, position: (817, 677, 933, 728))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/overflow_menu_icon, class: android.widget.ImageView, position: (933, 611, 1080, 738))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_frame, text: 2025_01_16_13_12_22.mp3, class: android.widget.FrameLayout, position: (0, 764, 1080, 933))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/item_holder, class: android.view.ViewGroup, position: (0, 764, 1080, 933))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_title, text: 2025_01_16_13_12_22.mp3, class: android.widget.TextView, position: (42, 796, 840, 851))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_duration, text: 00:09, class: android.widget.TextView, position: (840, 798, 933, 849))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_date, text: 16.01.2025, 01:12 PM, class: android.widget.TextView, position: (42, 851, 788, 902))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_size, text: 110.3 kB, class: android.widget.TextView, position: (788, 851, 933, 902))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/overflow_menu_icon, class: android.widget.ImageView, position: (933, 785, 1080, 912))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_frame, text: 2025_01_16_12_56_04.mp3, class: android.widget.FrameLayout, position: (0, 938, 1080, 1107))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/item_holder, class: android.view.ViewGroup, position: (0, 938, 1080, 1107))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_title, text: 2025_01_16_12_56_04.mp3, class: android.widget.TextView, position: (42, 970, 840, 1025))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_duration, text: 01:28, class: android.widget.TextView, position: (840, 972, 933, 1023))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_date, text: 16.01.2025, 12:57 PM, class: android.widget.TextView, position: (42, 1025, 848, 1076))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/recording_size, text: 1 MB, class: android.widget.TextView, position: (848, 1025, 933, 1076))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/overflow_menu_icon, class: android.widget.ImageView, position: (933, 959, 1080, 1086))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/trackView, class: android.widget.LinearLayout, position: (1012, 242, 1080, 1599))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_controls_wrapper, class: android.widget.RelativeLayout, position: (0, 1599, 1080, 2109))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_divider, class: android.view.View, position: (0, 1599, 1080, 1600))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_title, class: android.widget.TextView, position: (0, 1620, 1080, 1767))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_progress_current, text: 00:00, class: android.widget.TextView, position: (0, 1767, 146, 1878))Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_progressbar, class: android.widget.SeekBar, position: (146, 1767, 934, 1878))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_progress_max, text: 00:00, class: android.widget.TextView, position: (934, 1767, 1080, 1878))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/player_controls, class: android.widget.RelativeLayout, position: (0, 1878, 1080, 2109))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/previous_btn, content-desc: Previous, class: android.widget.ImageView, position: (204, 1878, 330, 2046))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/play_pause_btn, content-desc: Play / Pause, class: android.widget.ImageView, position: (456, 1878, 624, 2046))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/next_btn, content-desc: Next, class: android.widget.ImageView, position: (750, 1878, 876, 2046))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/main_tabs_holder, class: android.widget.HorizontalScrollView, position: (0, 2109, 1080, 2277))
Widget(text: Recorder, class: android.widget.LinearLayout, position: (0, 2109, 360, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_holder, class: android.widget.LinearLayout, position: (127, 2141, 233, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_icon, class: android.widget.ImageView, position: (143, 2141, 217, 2215))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_label, text: Recorder, class: android.widget.TextView, position: (127, 2215, 233, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_holder, class: android.widget.LinearLayout, position: (503, 2141, 577, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_icon, class: android.widget.ImageView, position: (503, 2141, 577, 2215))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_label, text: Player, class: android.widget.TextView, position: (504, 2215, 575, 2277))
Widget(text: Recycle Bin, class: android.widget.LinearLayout, position: (720, 2109, 1080, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_holder, class: android.widget.LinearLayout, position: (834, 2141, 966, 2277))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_icon, class: android.widget.ImageView, position: (863, 2141, 937, 2215))
Widget(resource-id: com.simplemobiletools.voicerecorder:id/tab_item_label, text: Recycle Bin, class: android.widget.TextView, position: (834, 2215, 966, 2277))
Widget(content-desc: Voice Recorder notification: Simple Voice Recorder, class: android.widget.ImageView, position: (107, 1, 165, 74))
Widget(content-desc: ATX notification: UIAutomator, class: android.widget.ImageView, position: (165, 1, 223, 74))
Widget(content-desc: Android System notification: , class: android.widget.ImageView, position: (223, 1, 281, 74))

 #History information (You should refer to the historical records to identify which part of the instructions they correspond to, consider the relationship between the current interface and the next step, and then update the instructions accordingly.):{
index-0: open the target appliaction

Here is the history of executed instructions:
}
**Warning:Ensure that the instructions have been completed; avoid performing the operation repeatedly.**

During task execution, please ensure whether you need to click the "Save" or "OK" button to save your actions.**If you have already clicked the "OK" or "Save" button, please disregard this prompt.**
You should tell me the updated instructions according this format.**Do not output any instructions regarding checking, review or verification, because you are an assistant and cannot perform such operations.**.(**Do not output any else except the json format.**)

        Note that: 
        Current state, finished step, error reason, revised method, revised method are less than 10 tokens.        error reason: When executed correctly, the error reason and revised method should be output as empty.
        next_instruction: next_instruction can only contain one instruction. If the task is completed, the next_instruction should be empty.

        {
        "explanation": {
            "current state" : "The current interface indicates that the search has been completed and the search results are displayed, but no flight has been selected yet.",
            "finished step" : "Based on the history, a search operation has already been performed. Therefore, 3. Search for available flights based on your preferences.",
            "error reason" : "The next action should select the flight",
            "revised method" : "add 4. Select the flight that suits your needs",
            "revised method": "4. Select the flight that suits your needs"
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
                ]
            }
        ]
            
        }
        If Task is finished, next_instruction = none

"""

    test_prompt2 = """
You are a smartphone assistant to help users complete tasks by interacting with mobile apps.Given a task, the previous UI actions, and the content of current UI state, your job is to decide whether the task is already finished by the previous actions, and if not, decide which UI element in current UI state should be interacted.
Task: use player to play 'test2.m4a'
Previous UI actions:
- launchApp Voice Recorder
- TapOn: <button text='Apps list'></button>
- TapOn: <button>go back</button>
- TapOn: <button text='Apps list'></button>
- TapOn: <button text='Apps list'></button>
Current UI state:
<button id=0 text='Apps list'></button>
<button id=1 text='Tuesday, Apr 1'>Tuesday, Apr 1</button>
<button id=2 text='File Manager'>File Manager</button>
<button id=3 text='Messages'>Messages</button>
<button id=4 text='Chrome'>Chrome</button>
<button id=5 text='Voice search<br>Search'></button>
<button id=6>go back</button>

Your answer should always use the following format: { "Steps": "...<steps usually involved to complete the above task on a smartphone>", "Analyses": "...<Analyses of the relations between the task, and relations between the previous UI actions and current UI state>", "Finished": "Yes/No", "Next step": "None or a <high level description of the next step>", "id": "an integer or -1 (if the task has been completed by previous UI actions)", "action": "tap or input", "input_text": "N/A or ...<input text>" }

**Note that the id is the id number of the UI element to interact with. If you think the task has been completed by previous UI actions, the id should be -1. If 'Finished' is 'Yes', then the 'description' of 'Next step' is 'None', otherwise it is a high level description of the next step. If the 'action' is 'tap', the 'input_text' is N/A, otherwise it is the '<input text>'. Please do not output any content other than the JSON format. **

"""

    start_time = time.time()
    result = query_qwen_vl_max_bailian(test_prompt)
    end_time =time.time()
    elapsed_time = end_time - start_time
    print(f"查询耗时：{elapsed_time:.2f} 秒")
    print(result)
    # print(query_qwen_72B_bailian(test_prompt))
