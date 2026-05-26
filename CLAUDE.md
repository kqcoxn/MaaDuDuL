# 项目信息

## 项目地址

https://github.com/kqcoxn/MaaDuDuL

## 必要的信息

- 项目使用 pipeline + custom 双协议辅助，custom 即 agent 的内容，agent 相当于 custom 的 server
- 本项目自封装了很多 custom 的操作，若已有封装则优先使用本项目的封装
- 本项目使用 maafw python binding 作为 custom 的语言
- 本项目 UI 使用 MFAAvalonia，简称 mfaa

## 应该做的事

- 当涉及 maafw 的 pipeline 或 custom api 时，应该参阅相关 `/dev/instructions/` 下的参考文档，不要凭空生成
- custom 输出应该使用 `Prompter.log()` 
- 使用`yarn`作为 Node.js 的包管理器

## 禁止的工作

- 不要帮我`yarn dev`，一般我是一直开着的
- 不要自动帮我构建测试相关内容
- 不要主动写 Pipeline JSON，如果需要扩充功能，在最后给我流水线汇总
- 本地的 `/MFAAvalonia` 是测试环境，不应该改动，修改各资源应该在 `/assets` 中


# 可用参考

## 说明

maaframework 可缩写为 mfw、maafw，包括了 pipeline 与 custom 的相关内容

## 目录

- **mfw使用方式/pipeline相关**: `/dev/instructions/maafw-guide/`

## 其他

当需要其他 API 但本地没有时可视情况自动网络检索