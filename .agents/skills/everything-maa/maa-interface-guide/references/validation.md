# Interface 验证流程

## 1. 发现项目约定

先检查 schema 关联、包管理器、lockfile、`package.json` scripts、`packageManager` 字段、`maatools.config.mts`、CI 配置和项目文档。运行 `maa-tools` 前必须确认 `package.json` 中是否有现成脚本，并确认 `packageManager` 字段或 lockfile 对应的包管理器（npm、pnpm、yarn 或 bun）。优先运行项目已经定义并锁定版本的命令，不猜测工具名称或参数；禁止直接执行 `node_modules` 内文件。

## 2. 静态验证阶梯

1. 用适合 JSON 或 JSONC 的解析器检查语法；不要用严格 JSON 解析器误判合法 JSONC。
2. 使用目标项目已有的 Interface schema 校验主文件及 import/config 文件。
3. 检查所有本地路径是否按协议基准解析且目标存在。
4. 建立声明与引用集合，逐 controller/resource 组合检查唯一性、存在性、过滤适用性、task entry 和 i18n 完整性。
5. 检查 `pipeline_override` 目标节点是否存在，但不在本 skill 中修改 Pipeline。

每一层都记录采用的文件、命令和结果。

## 3. maa-tools

社区的 [`@nekosu/maa-tools`](https://github.com/neko-para/maa-support-extension)可加载 Interface bundle，遍历 controller/resource 组合，执行跨文件诊断并尝试加载资源。

若项目已安装或已有 script，优先运行 `package.json` 中已有的 script；没有 script 时，用与 lockfile 一致的包管理器调用已锁定依赖。先检查命令是否会写日志、缓存、快照或其他文件；解释或只读审查不授权这些写入，存在写入时先询问用户。禁止直接执行 `node_modules/.bin` 或 `node_modules/@nekosu/maa-tools` 中的文件。典型命令形态为：

```text
npx --no-install @nekosu/maa-tools check [maatools.config.mts]
```

具体参数以项目 script、已安装包的 `--help` 或配置为准。

项目使用 pnpm 时优先 `pnpm exec`，yarn 时优先 `yarn exec`，bun 时优先 `bun x`；需要临时下载时再使用对应的 `pnpm dlx`、`yarn dlx` 或 `bunx`，以项目实际锁定的依赖为准。

若项目未安装该包：

1. 根据 `package.json` 的 `packageManager` 字段和 lockfile 确认项目包管理器，并说明临时执行可能访问网络并下载包；
2. 询问用户是否允许执行；
3. 只有获得许可后，才运行与项目包管理器一致的临时命令（例如 npm 的 `npx @nekosu/maa-tools check [config-path]`、pnpm 的 `pnpm dlx @nekosu/maa-tools check [config-path]`）；
4. 不以 `npx ... init` 创建配置，除非用户另行明确要求；
5. 用户拒绝时不阻塞其他静态检查，但在结论中标记语义诊断未执行。

`maa-tools check` 可能加载 MaaFramework 和资源并写入日志。运行前检查配置、工作目录和日志路径；只读模式下未经许可不得产生这些文件。它不连接设备或执行 Pipeline，但资源加载失败属于阻断结果。

## 4. 严重级别

必须阻断完成：解析/schema error、重复声明、未知引用、无效 task entry、缺失语言键、错误 preset 类型、资源加载失败。

warning 不自动阻断，但必须归类并给出依据。若 warning 实际意味着某 controller/resource 组合不可运行，则提升为阻断项。

## 5. 报告模板

```yaml
mode: explain | review | modify
interface_version: 2
protocol_source: <项目 schema、tag、commit 或官方 URL>
changed_files: []
checks:
  - name: <检查名>
    command: <命令或 null>
    result: pass | warning | fail | skipped
    evidence: <简要证据>
blocking_issues: []
warnings: []
unverified: []
```
