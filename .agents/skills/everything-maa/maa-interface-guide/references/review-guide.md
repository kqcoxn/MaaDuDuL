# Interface V2 审查指南

## 来源优先级

1. 目标项目已关联或 vendored 的 `interface.schema.json`、`interface_import.schema.json`、`interface_config.schema.json`。
2. 目标项目锁定的 MaaFramework tag、commit、依赖版本或模板版本。
3. [MaaFramework 官方仓库](https://github.com/MaaXYZ/MaaFramework)中对应版本的原始 Project Interface V2 文档与 `tools/interface*.schema.json`。
4. 社区工具的诊断结果和真实项目写法，仅作补充证据，不覆盖官方 schema。

`interface_version: 2` 与 PI 扩展能力语义版本是两层版本。项目证据冲突时先报告差异，不静默改用 `main`。无法确定版本时说明假设，并避免使用仅见于更新协议的字段；schema 与 PI 文档不一致时分别记录，不要把文档写法当成 schema 已验证。

## 协议来源发现

本仓库不维护 Project Interface V2 的字段矩阵、版本能力表或语义快照。需要上游依据时按以下流程发现并引用：

1. 通过 `$maa-wiki` 加载 MaaLLMWiki 上游 `maallmwiki` skill，找到 Project Interface V2 文档和 `interface*.schema.json` 对应的入口；仅当上游 skill 不可达时，按 `$maa-wiki` 的披露顺序用根 README 降级。
2. 采用该入口记录的 pinned tag、commit 或 revision，回到 MaaFramework 官方仓库读取原始文档与 schema。
3. 没有项目内证据时不要凭模型记忆补字段；找到的每个事实记录 URL 或 revision。
4. MaaLLMWiki 路径不可达或 revision 不明确时，把相关 PI 语义标记为未验证，并继续完成可核实的项目文件检查。

官方文件路径可能随上游重构变化，不要把历史路径或本地引用写成永久协议来源。

## 文件边界

从主 `interface.json` / `interface.jsonc` 出发，递归读取其直接或间接 import、languages 指向的文件和项目已有的 Interface 配置。路径均以协议规定的基准目录解析，不以当前 shell 目录猜测。

允许修改：

- 主 Interface；
- Interface import；
- languages 指向的翻译文件；
- 项目已有的 Interface 配置文件。

只读核实：Pipeline、Python Agent、pretask 可执行程序、图片、可执行文件和构建配置。

## 引用闭环

逐类建立 declaration/reference 表并检查唯一性、存在性和适用性：

| 声明 | 常见引用位置 | 重点检查 |
| --- | --- | --- |
| controller | resource、task、option、preset、pretask | 名称唯一，过滤条件有交集 |
| resource | task、option、preset、pretask、hash、配置 | path/`attach_resource_path` 存在，controller 组合有效 |
| group | task.group、展示顺序 | 声明存在，分组不悬空 |
| task | task entry、preset、setting | entry 在适用资源中存在 |
| option | global/resource/controller/task/setting/pretask/preset | 类型、case/input/hotkey、过滤条件一致 |
| case/input | default、preset、pretask 参数、占位符 | 名称和取值类型匹配所属 option；password 禁止 default/preset |
| pretask | exec、args、resource/controller、option | 名称和引用可解析，主文件加 import 执行顺序明确 |
| setting | option | 分区键唯一，引用 option 存在且适用 |
| locale key | 所有支持国际化的字符串 | 每种声明语言均存在 |

对每个 controller/resource 组合分别求解，不能只看全局合并后的“存在”。某个引用在另一资源中存在，不代表当前组合有效。

## Option 边界

本 skill 可以新增、修改或修复 Interface 侧的 option、case、input、默认值、过滤器和引用。出现以下任一情况时接力 `$maa-pipeline-option`：

- 新增或改变 `pipeline_override` 行为；
- 需要确认被覆盖节点是否预定义及字段路径是否正确；
- Python 读取 `context.get_node_data()` 或 Custom 参数；
- option 的关闭状态需要影响实际执行链。

`pipeline_override` 是对已加载节点的覆盖，不应被当成创建 Pipeline 节点的手段。

## 常见高风险点

- 每个 controller 的 `display_short_side`、`display_long_side`、`display_expand`
  和 `display_raw` 是互斥的分辨率策略；都不配置时，PI 运行时使用短边 720。
  改成 `display_raw` 会脱离 Pipeline 模板和 ROI 的 720p 基准，不能作为普通
  跨设备适配方案。资源包之间的设备差异应先核对 controller/resource 组合，
  不要把某个模拟器 raw 截图上的坐标复制到另一个 controller。
- import 后出现重复 controller/resource/group/option/case/input 声明；
- task.entry 只在部分 resource 中存在；
- controller/resource 过滤导致 option 或 preset 在当前组合不可用；
- preset 值与 select/switch、checkbox、input 的期望类型不符；
- `$locale_key` 只在部分语言中定义；
- 把 `interface_version: 2` 当成所有 PI v2.x 字段都可用的证明；
- schema 滞后时把文档允许字段误报为结构错误，或反向把 schema 能解析误当成运行时支持；
- 相对路径基准理解错误或使用反斜杠造成跨平台问题；
- `resource.hash` 覆盖范围或校验时机错误，`attach_resource_path` 被计入主资源 hash；
- pretask 执行顺序、CWD、最后一参数 JSON 或 controller/resource 过滤与目标 Client 不一致；
- Agent 子进程假设 `PI_*` 全部存在，或把 `PI_INTERFACE_VERSION` 与 `interface_version: 2` 混淆；
- password 字段进入 `default` 或 `preset`，或 pretask 参数、日志、遥测泄漏明文；
- 已配置 telemetry 但未处理用户授权、调试禁用、`focus.trace` 默认值或敏感内容采样；
- 为修复 Interface 而越界改动 Pipeline/Python；
- 将某个社区项目的历史写法误当成当前官方协议。
