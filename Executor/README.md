# 仓库说明
这个仓库是执行器的代码，也就是输入是`task`，执行后改仓库就会正常执行。

# 运行说明

1. 准备UI Map.
   
   首先你运行另一个仓库并生成UI Map，然后在`config.py`里面设置：

```python
ui_map_path = "D:/code/AndroidSourceCodeAnalyzer/code_maps/applauncher.json"
```

将这个ui_map_path设置为你的ui_map。

2. 设置任务.
    找到目录下`task.json`里面：

```json
{
"app_name": "Simple-App-Launcher",
"apk_name": "com.simplemobiletools.applauncher",
"task_names": [
    "search 'Clock' app and open it"
]
}
```

我们在`total_task`里面写好了数据集中的task，你只需要复制进来就好了。
当然，我们也支持批量任务执行（仅限制单个app），但是暂时不支持多app一起执行。
如直接配置`task.json`如下：
```
{
    "app_name": "Simple-Notes",
    "apk_name": "com.simplemobiletools.notes.pro",
    "task_names": [
      "Create a text note named 'NewTextNote'",
      "Create a checklist note called 'NewCheckList'",
      "Delete the note 'Diary'",
      "Create a new note called 'test' and type '123456'",
      "Rename the note 'diary' to 'events'",
      "Adjust the fontsize of the Notes app to 125%",
      "Print 'Diary' as diary.pdf",
      "Set app theme to light and save it",
      "Disable autosave notes",
      "Create a text note called 'test', type '12345678', and search for '234'",
      "Change the alignment to center",
      "Show the number of words in the Notes app",
      "Create a checklist named 'test' and sort the items by creating date"
    ]
  }
```

3. 配置Atx-agent

启动你的虚拟机，我们假设设备为`emulator-5554`，可以使用`adb devices`查看。

```bash
# 推送 atx-agent 到设备
adb -s emulator-5554 push atx-agent /data/local/tmp/

# 赋予执行权限
adb -s emulator-5554 shell chmod 755 /data/local/tmp/atx-agent

# 启动 atx-agent
adb  -s emulator-5554 shell  /data/local/tmp/atx-agent server -d
```

这时候你的设备上会多一个小车的图标的APP，这个就是Atx-agent。
**长时间不运行可能UIAutomator会自动停止服务，设备没运行/关机可能会导致Atx-Agent服务停止**。当你程序产生Bug时，请确认小车APP中，这两个是在运行的，而不是Stop。

如果Atx-Agent停止了，可以直接运行
```bash
adb  -s emulator-5554 shell  /data/local/tmp/atx-agent server -d
```
如果UIAutomator停止了，手动在APP中打开这个服务就好了。


3. 运行任务
执行如下命令：
```bash
python run_command.py
```
或者指定设备，这在并行运行实验的时候非常有用。
```bash
python run_command.py --port emulator-5554
```

4. 查看结果
会在`output`中生成结果，log和相关截图。

# 配置说明

我们请默认使用
```python
run_method=code_aware_method # 使用我们的方法。
uimanual=True # 使用UI Map
adapting=True # 使用adapting
wtg=False # 不使用WTG
main_activity = "com.simplemobiletools.applauncher.activities.SplashActivity" # 当前还需要设置一下Main，这个自动化很容易，我一会儿弄弄

```

## Cite Guardian work
If your find this work useful, please consider cite the following paper because we build the tool based on Guardian:

```
@inproceedings{ran2024guardian,
author = {Ran, Dezhi and Wang, Hao and Song, Zihe and Wu, Mengzhou and Cao, Yuan and Zhang, Ying and Yang, Wei and Xie, Tao},
title = {Guardian: A Runtime Framework for LLM-Based UI Exploration},
year = {2024},
isbn = {9798400706127},
publisher = {Association for Computing Machinery},
address = {New York, NY, USA},
url = {https://doi.org/10.1145/3650212.3680334},
doi = {10.1145/3650212.3680334},
booktitle = {Proceedings of the 33rd ACM SIGSOFT International Symposium on Software Testing and Analysis},
pages = {958–970},
numpages = {13},
series = {ISSTA 2024}
}
```


