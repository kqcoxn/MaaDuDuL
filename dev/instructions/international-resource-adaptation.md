# International Resource Adaptation Guide

This document is for contributors who adapt MaaDuDuL to the international server.

The goal is to explain the adaptation model used by this repository and how it maps to MaaFramework ProjectInterface and resource-loading rules.

## Scope

This guide focuses on:

- ProjectInterface resource definitions
- resource path overlay rules
- pipeline-level overrides for OCR and UI differences
- image / model / package-name overrides
- when to touch `agent/` and when not to

This guide does not explain MaaFramework from scratch. When you need protocol details, read the upstream references in:

- [3.3-ProjectInterfaceV2协议.md](D:/_Projects/MaaDuDuL/dev/instructions/maafw-guide/3.3-ProjectInterfaceV2协议.md)
- [3.1-任务流水线协议.md](D:/_Projects/MaaDuDuL/dev/instructions/maafw-guide/3.1-任务流水线协议.md)
- [4.2-标准化接口设计.md](D:/_Projects/MaaDuDuL/dev/instructions/maafw-guide/4.2-标准化接口设计.md)

## Current Layout

This repository uses one shared task set and multiple resource paths.

- Base resource: `assets/resource/base`
- China server resource: `assets/resource/base`
- English / international overlay: `assets/resource/en`
- Shared task definitions: `assets/resource/tasks`
- Chinese locale strings: `assets/locales/interface_zh.json`
- English locale strings: `assets/locales/interface_en.json`

The relevant `interface.json` resource layout is:

```jsonc
"resource": [
    {
        "name": "cn",
        "label": "$resource_cn_label",
        "path": ["./resource/base"]
    },
    {
        "name": "en",
        "label": "$resource_en_label",
        "path": ["./resource/base", "./resource/en"]
    }
]
```

This means:

- `cn` loads only the base resource.
- `en` loads the base resource first, then loads `assets/resource/en` as an override layer.

This follows MaaFramework ProjectInterface V2 resource loading rules: later paths override earlier paths.

## Important Project Rule

Do **not** duplicate the task layer for each server unless there is a real protocol-level reason.

In this repository:

- `assets/resource/tasks` is shared
- task entry names stay shared
- most adaptation work should happen in resource overlays

That is the intended model.

If the international server differs from the China server, prefer:

1. OCR `expected` override
2. template image override
3. pipeline node override
4. package / app identifier override
5. only then, `agent/` logic changes if the runtime behavior truly differs

Do **not** start by copying the whole task set or rewriting all pipeline files.

## How Resource Overlay Works

MaaFramework merges resources by loading multiple resource directories in order.

For this project, the international resource works like this:

1. Load `assets/resource/base`
2. Load `assets/resource/en`
3. Files in `en` override matching files from `base`

The most common override targets are:

- `pipeline/...`
- `image/...`
- `model/...`

Do not point a ProjectInterface resource path directly at `pipeline/` only. Follow the MaaFramework recommendation and keep the full resource tree structure.

## How To Override a Pipeline Node

If a node differs only in OCR text or a few fields, create a file with the same relative path under `assets/resource/en`.

Example source file:

- base: `assets/resource/base/pipeline/日常任务/领取邮件.json`

Example override file:

- en: `assets/resource/en/pipeline/日常任务/领取邮件.json`

Use the same node names and override only the fields that differ.

Example:

```json
{
    "领取邮件_没有邮件": {
        "recognition": {
            "param": {
                "expected": ["No mail to claim"]
            }
        }
    },
    "领取邮件_确保进入邮件面板": {
        "recognition": {
            "param": {
                "expected": ["Mailbox"]
            }
        }
    },
    "领取邮件_确认领取": {
        "recognition": {
            "param": {
                "expected": ["Tap the screen to continue"]
            }
        }
    },
    "领取邮件_领取奖励": {
        "recognition": {
            "param": {
                "expected": ["Claim"]
            }
        }
    }
}
```

Use this style when:

- node names are the same
- flow is the same
- only OCR / template / target parameters differ

## When To Override Images Instead of OCR Text

If the international server uses:

- different icons
- different button shapes
- different localized UI labels that OCR handles poorly

prefer image/template overrides under:

- `assets/resource/en/image/...`

This is usually more stable than forcing OCR for small UI labels.

## When To Override Package Names

If the app package / bundle identifier differs between regions, do not hardcode it in task definitions.

Check these places first:

- `assets/resource/base/pipeline/日常任务/启动游戏.json`
- `assets/resource/base/pipeline/日常任务/关闭游戏.json`
- `assets/interface.json` controller definitions, if applicable

If only the international resource differs, override the affected pipeline nodes in `assets/resource/en/pipeline/...`.

## Locale and Descriptions

ProjectInterface labels and task descriptions are localized separately from the runtime resource overlay.

Current files:

- `assets/locales/interface_zh.json`
- `assets/locales/interface_en.json`

Use locales for:

- resource labels
- controller labels
- group labels
- task labels
- task option labels
- task description path mapping

Use resource overlay for:

- runtime OCR text
- template images
- pipeline actions and recognition parameters

These are different layers. Do not mix them up.

## English Task Descriptions

This repository already maps English task descriptions through locale entries such as:

```jsonc
"Resource/descs/daily/claim_mail.md": "Resource/descs_en/daily/claim_mail.md"
```

That means:

- shared task config can still reference `Resource/descs/daily/...`
- the English locale rewrites it to `Resource/descs_en/...`

If you add a new task description:

1. add the Chinese file under `assets/resource/descs/...`
2. add the English file under `assets/resource/descs_en/...`
3. map the English locale key in `assets/locales/interface_en.json`

## When Agent Changes Are Needed

Most regional adaptation should stay inside resource files.

Only touch `agent/` when:

- the server changes the runtime flow in a way pipeline-only logic cannot express
- OCR text needs dynamic handling beyond normal pipeline overrides
- a custom action / custom recognition depends on server-specific logic

If you modify `agent/`:

- this project uses the MaaFramework Python binding
- custom output should use `Prompter.log()`
- prefer existing helper wrappers already present in this repository

Before changing custom logic, review:

- `agent/customs/...`
- `agent/customs/utils/prompter.py`
- `agent/customs/maahelper/...`

And keep upstream MaaFramework guidance in mind, especially the standardized interface notes in:

- [4.2-标准化接口设计.md](D:/_Projects/MaaDuDuL/dev/instructions/maafw-guide/4.2-标准化接口设计.md)

## Recommended Adaptation Workflow

For each international-server issue:

1. Find the base task or pipeline node that fails.
2. Check whether the difference is:
   - OCR text
   - image/template
   - click target / ROI
   - package / app identifier
   - actual business logic
3. If it is resource-level, add the smallest possible override under `assets/resource/en`.
4. Keep the shared task layer unchanged unless there is no other clean option.
5. If you add new user-facing strings, update `assets/locales/interface_en.json`.

## What Not To Do

Avoid the following:

- duplicating the whole task layer for each server
- copying the whole `base` resource tree into `en`
- modifying `MFAAvalonia/` directly
- changing `agent/` first when a resource override would be enough
- hardcoding English-only behavior into shared task definitions

## Quick Checklist

Before opening a PR, verify:

- the change is placed in `assets/resource/en` when it is server-specific
- the shared task layer is still shared unless duplication is truly required
- any new UI string has a locale entry
- any new English description file exists under `assets/resource/descs_en`
- package / OCR / template changes are documented in the PR notes

## Minimal Example in This Repository

See this existing example override:

- [assets/resource/en/pipeline/日常任务/领取邮件.json](D:/_Projects/MaaDuDuL/assets/resource/en/pipeline/日常任务/领取邮件.json:1)

It demonstrates the intended adaptation style:

- same node names
- same task flow
- only localized OCR expectations overridden

**However, the content in this document is simulated and does not reflect the actual situation. It needs to be checked against the game again!**