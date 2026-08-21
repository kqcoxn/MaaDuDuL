# Interface V2 审查指南

## 来源优先级

1. 目标项目已关联或 vendored 的 `interface.schema.json`、`interface_import.schema.json`、`interface_config.schema.json`。
2. 目标项目锁定的 MaaFramework tag、commit、依赖版本或模板版本。
3. [MaaFramework 官方仓库](https://github.com/MaaXYZ/MaaFramework)中对应版本的 `docs/zh_cn/3.3-ProjectInterfaceV2协议.md` 与 `tools/interface*.schema.json`。
4. 社区工具的诊断结果和真实项目写法，仅作补充证据，不覆盖官方 schema。

项目证据冲突时先报告差异，不静默改用 `main`。无法确定版本时说明假设，并避免使用仅见于更新协议的字段。

## 文件边界

从主 `interface.json` / `interface.jsonc` 出发，递归读取其直接或间接 import、languages 指向的文件和项目已有的 Interface 配置。路径均以协议规定的基准目录解析，不以当前 shell 目录猜测。

允许修改：

- 主 Interface；
- Interface import；
- languages 指向的翻译文件；
- 项目已有的 Interface 配置文件。

只读核实：Pipeline、Python Agent、图片、可执行文件和构建配置。

## 引用闭环

逐类建立 declaration/reference 表并检查唯一性、存在性和适用性：

| 声明 | 常见引用位置 | 重点检查 |
| --- | --- | --- |
| controller | resource、task、option、pretask | 名称唯一，过滤条件有交集 |
| resource | task、option、preset、配置 | 路径存在，controller 组合有效 |
| group | task.group、展示顺序 | 声明存在，分组不悬空 |
| task | task entry、preset、setting | entry 在适用资源中存在 |
| option | 全局/controller/resource/task/setting/preset | 类型、case/input、过滤条件一致 |
| case/input | default、preset、占位符 | 名称和取值类型匹配所属 option |
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

- import 后出现重复 controller/resource/group/option/case/input 声明；
- task.entry 只在部分 resource 中存在；
- controller/resource 过滤导致 option 或 preset 在当前组合不可用；
- preset 值与 select/switch、checkbox、input 的期望类型不符；
- `$locale_key` 只在部分语言中定义；
- 相对路径基准理解错误或使用反斜杠造成跨平台问题；
- 为修复 Interface 而越界改动 Pipeline/Python；
- 将某个社区项目的历史写法误当成当前官方协议。
