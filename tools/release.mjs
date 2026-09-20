import {readFileSync} from "node:fs";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

process.chdir(fileURLToPath(new URL("../", import.meta.url)));
const {project} = JSON.parse(readFileSync("maa-project.json", "utf8"));
if (!/^\d+\.\d+\.\d+(?:-[\w.-]+)?$/.test(project.version)) throw new Error("Invalid project version");
const tag = `v${project.version}`;
for (const [
    command,
    args,
] of [
    [
        process.execPath,
        [
            "tools/versions.mjs",
            "--check",
        ],
    ],
    [
        "git",
        [
            "tag",
            "-a",
            tag,
            "-m",
            `release ${tag}`,
        ],
    ],
    [
        "git",
        [
            "push",
            "origin",
            tag,
        ],
    ],
]) {
    const result = spawnSync(command, args, {stdio: "inherit"});
    if (result.error || result.status !== 0) process.exit(result.status || 1);
}
