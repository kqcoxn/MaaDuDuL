---
trigger: always_on
alwaysApply: true
---

## 项目地址

https://github.com/kqcoxn/MaaDuDuL

## 必要的信息

- 项目使用 pipeline + custom 双协议辅助，custom 即 agent 的内容，agent 相当于 custom 的 server
- 本项目自封装了很多 custom 的操作，若已有封装则优先使用本项目的封装
- 本项目使用 maafw python binding 作为 custom 的语言

## 应该做的事

- 当涉及 maafw 的 pipeline 或 custom api 时，应该参阅相关 `/instructions/` 下的参考文档，不要凭空生成
- custom 输出应该使用 `Prompter.log()` 
- 使用`yarn`作为 Node.js 的包管理器

## 禁止的工作

- 不要帮我`yarn dev`，一般我是一直开着的
- 不要自动帮我构建测试相关内容
