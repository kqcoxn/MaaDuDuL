---
name: maa-interface-guide
description: 解释、审查、诊断和修改已有 MaaFramework Project Interface V2。用于处理现有 interface.json / interface.jsonc、Interface import、controller、resource、task、group、option、preset、setting、国际化、路径与跨文件引用，或执行 schema 与 maa-tools 校验；不用于创建新项目、从零生成 Interface 或支持 Project Interface v1。
---

# Maa Interface V2 工作流

只处理已存在的 Project Interface V2。先确定用户要求的是解释、审查/诊断还是修改；只读请求不得改文件。

## 建立事实基线

1. 在目标项目中定位 `interface.json` 或 `interface.jsonc`。不存在时停止，要求先使用 `$maa-project-create` 创建项目；不得生成孤立的 Interface。
2. 读取 `interface_version`。只接受 V2；缺失、为 1 或呈现 v1 结构时报告不支持，不提供迁移或兼容写法。
3. 先读取目标项目已有的 schema 关联、MaaFramework 版本锁、`maatools.config.mts`、Interface import 和语言文件。项目内证据优先于本 skill 的经验。
4. 若项目没有足够的协议依据，再查 [MaaFramework 官方仓库](https://github.com/MaaXYZ/MaaFramework)当前对应版本的文档与 `tools/interface*.schema.json`。记录实际采用的 tag、commit、schema 路径或 URL；不要依赖个人机器上的 MaaFramework 绝对路径。
5. 保留目标文件现有的 JSON/JSONC、缩进、字段排序、命名和拆分风格，除非用户明确要求统一格式。

需要检查字段选择与引用关系时读取 [references/review-guide.md](references/review-guide.md)。需要选择和运行验证工具时读取 [references/validation.md](references/validation.md)。

## 操作模式

### 解释

只读主文件、import、语言文件及相关 Pipeline 入口，说明 controller、resource、task、group、option、preset 和 setting 的实际关系。区分“schema 允许”“Client 可能支持”和“当前项目确实使用”，不要把推断表述成事实。

### 审查或诊断

按以下顺序检查并报告带文件位置的证据：

1. V2 版本与 schema 合法性；
2. import、资源路径、图标、语言文件等路径是否可解析；
3. controller、resource、group、task、option、case、input、preset 和 locale 引用是否存在且唯一；
4. controller/resource 过滤后，task、option、preset 与 setting 是否仍然适用；
5. task entry 是否能在所选资源的 Pipeline 中解析；
6. `pipeline_override` 是否只覆盖已存在的节点；
7. Interface 配置和多语言内容是否完整；
8. 项目已有校验工具的诊断结果。

审查请求默认不修复。区分协议错误、跨文件语义错误、Client 兼容风险和维护性建议。

### 修改

1. 先列出受影响的声明、引用和 controller/resource 组合。
2. 仅修改主 Interface、其 import、语言文件和 Interface 配置文件。
3. 做最小闭环修改；同步更新允许范围内的引用和翻译，不顺手重排无关字段。
4. Pipeline、Python Agent、图片和构建配置只读。需要修改这些文件时按“技能接力”处理。
5. 修改后执行“验证与完成标准”。

## 技能接力

- 目标项目或 Interface 不存在：停止并使用 `$maa-project-create`；本 skill 不创建项目或 Interface。
- option 的 Interface 声明由本 skill 负责；一旦涉及 `pipeline_override` 行为、目标 Pipeline 节点或 Python 参数读取，使用 `$maa-pipeline-option`。
- Pipeline 节点、识别、动作或状态流设计使用 `$maa-pipeline-guide`；行为验证使用 `$maa-pipeline-testing`；关系可视化使用 `$maa-pipeline-graph`。
- 用户要求完整功能时，可以显式接力对应 skill 并继续闭环。用户只要求 Interface 审查或修改时，不得扩大写入范围，只报告跨边界问题。

## 验证与完成标准

按 [references/validation.md](references/validation.md) 从低成本到高成本验证：JSON/JSONC 解析、项目 schema、路径与引用、项目已有检查命令、可选的 `maa-tools` 语义诊断。运行 `maa-tools` 前先检查 `package.json` 中已有的脚本和项目实际使用的包管理器；有项目脚本或已安装依赖时使用项目锁定命令，禁止直接执行 `node_modules` 内文件。静态编辑不得自动连接设备或执行 Pipeline。解释或只读审查中，若检查命令会写日志、缓存或其他文件，必须先取得用户许可。

若项目未安装 `@nekosu/maa-tools`，先按项目 lockfile 对应的包管理器确认临时执行方式，并必须先询问用户是否允许下载或执行；未获许可不得运行、安装或下载。用户拒绝时继续完成其余静态检查，并明确记录缺失的诊断层。

完成条件：

- error 已修复，否则任务保持未完成并说明阻塞；
- warning 逐条标为已处理、项目有意保留、工具误报或待确认；
- 未知引用、缺失 i18n、无效 task entry、重复名称和资源加载失败始终按阻断项处理；
- 报告改动文件、采用的协议/schema 来源、运行的命令、结果及未执行的验证。

不要把“JSON 能解析”或“schema 通过”单独当作 Interface 正确性的证明。
