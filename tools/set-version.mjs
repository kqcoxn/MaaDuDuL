import {readFileSync, writeFileSync} from "node:fs";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const args = process.argv.slice(2);
const usage = "用法：yarn version:set <版本号>（例如 1.2.3、v1.2.3 或 1.2.3-beta.1）";

if (
    args.length === 1 &&
    [
        "--help",
        "-h",
    ].includes(args[0])
) {
    console.log(usage);
    process.exit(0);
}

const version = args[0]?.replace(/^v/, "");
// 同时用于 Node 和 Python 项目，仅接受两者都支持的正式版和常用预发布版。
if (
    args.length !== 1 ||
    !/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-(?:alpha|beta|rc)\.(0|[1-9]\d*))?$/.test(version ?? "")
) {
    console.error(usage);
    process.exit(1);
}

let written = false;
try {
    const path = new URL("../maa-project.json", import.meta.url);
    const source = readFileSync(path, "utf8");
    const config = JSON.parse(source);
    const previous = config.project.version;
    if (previous !== version) {
        config.project.version = version;
        const newline = source.includes("\r\n") ? "\r\n" : "\n";
        const content = (JSON.stringify(config, null, 4) + "\n").replaceAll("\n", newline);
        writeFileSync(path, content);
        written = true;
    }
    console.log(`项目版号：${previous} → ${version}`);

    // 复用统一同步入口，包含派生配置、Python 锁文件和 requirements 导出。
    for (const mode of [
        "--sync",
        "--check",
    ]) {
        const result = spawnSync(
            process.execPath,
            [
                "tools/versions.mjs",
                mode,
            ],
            {
                cwd: root,
                stdio: "inherit",
            },
        );
        if (result.error || result.status !== 0) {
            throw new Error(
                `版本${mode === "--sync" ? "同步" : "检查"}失败：${result.error?.message ?? result.signal ?? result.status}`,
            );
        }
    }
    console.log(`版号已更新为 ${version}，同步及一致性检查通过。`);
} catch (error) {
    console.error(error.message);
    if (written) console.error(`maa-project.json 已更新为 ${version}。`);
    console.error("已发生的修改会保留；修复错误后执行 yarn versions:sync && yarn versions:check。");
    process.exitCode = 1;
}
