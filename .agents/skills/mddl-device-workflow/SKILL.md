---
name: mddl-device-workflow
description: MaaDuDuL 模拟器检查、直接操作与实机验收的工具分工。用于查看设备状态、截图观察、界面导航和观察自动对局；常规检查及直接操作优先原生 ADB，编辑 Pipeline 的识别、坐标和点击验证使用 MaaFramework。项目维护的约定，不修改 everything-maa 上游技能。
---

# MaaDuDuL 实机操作分工

本 skill 由项目维护，存放在 `everything-maa` 外，避免更新上游技能时丢失用户约定。

## 选择执行入口

- **常规检查、探索和直接操作**：优先直接调用模拟器 ADB，包括设备状态、截图、页面导航、点击和滑动。无需为观察画面启动 MaaFramework Tasker、Agent 或 OCR 流程。
- **修改 Pipeline 后的截图、识别与点击验证**：使用项目 MaaFramework/MaaMCP 或 maafw-cli，确认实际控制器的截图缩放、ROI、模板、动作目标及 Custom 接线。常规 ADB 截图不能替代这些验证证据。
- **验收现有自动任务**：运行真实 Pipeline + Custom，常规观察用 ADB 旁路截图和本地日志。观察期间不要另起一套自动点击与运行中的 Tasker 争用设备；需要接管时先停掉原任务。

## ADB 观察与直接操作

从当前环境的模拟器安装配置、已有连接或 PATH 定位 `adb`，用 `adb devices -l` 核实目标。沿用用户已选定且仍可确认的设备；同一模拟器可能同时出现 TCP 和 `emulator-*` 两个连接标识，不把端口写成永久默认值。确有多个无法区分的目标时再询问用户。

每次调用显式指定 `-s SERIAL`。常规命令示例：

```text
adb -s SERIAL exec-out screencap -p
adb -s SERIAL shell input tap X Y
adb -s SERIAL shell input swipe X1 Y1 X2 Y2 DURATION_MS
```

截图通过二进制 stdout 保存。不要用会改变 PNG 字节的文本管道或旧版 PowerShell 的文本重定向。可使用本 skill 的无第三方依赖脚本：

```text
python .agents/skills/mddl-device-workflow/scripts/adb_capture.py --adb ADB_PATH --serial SERIAL --output OUTPUT.png
```

脚本输出 JSON，含原图宽高、路径和耗时。ADB 点击坐标使用设备原始分辨率；如果观察图经过缩放，按实际原图与观察图尺寸换算。不要直接套用 Pipeline 的 1280×720 坐标。Pipeline 资源所用截图仍通过 MaaFramework 验证。

## 实机对局验收

执行前记录所在页面、次数和点数；任务结束后确认实际结算与稳定返回页。严格按用户指定局数执行，不因工具超时、截图失败或修复脚本而重新入场。

正式匹配有真实对手，不能让对手等待代码适配。发现必须修改代码、重启 Agent 或长时间排查的问题时，立即停止调试，先通过可用的求和/结束入口结束当前对局；没有求和入口则投降。先完成退出，再在大厅或离线修复、验证。不要把正在匹配的对手当作调试环境，也不要在修代码期间放任倒计时、黄牌或自动操作反复消耗对方时间。对局终止后只有用户已授权继续开局时才再开；单纯修复不自动增加实战局数。

MCP 请求超时不代表原生 Tasker 已停止。查看任务事件和 ADB 当前画面，确认状态后再决定接回当前局或收尾。需要等待时采用短轮询，并继续向用户报告有意义的进展。

MaaMCP 运行过 Pipeline 后，完成或接管时调用 `stop_pipeline` 清理 Tasker/Agent。创建的临时观察进程也要正常退出。修改资源仍只在 `/resource`、任务在 `/tasks`，不修改 `/MFAAvalonia`，不自动启动 `yarn dev` 或构建测试环境。
