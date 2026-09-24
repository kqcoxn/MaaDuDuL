import {readFileSync, writeFileSync, appendFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {spawnSync} from "node:child_process";

const root = fileURLToPath(new URL("../", import.meta.url));
process.chdir(root);
const read = (path) => readFileSync(path, "utf8").replaceAll("\r\n", "\n");
const config = JSON.parse(read("maa-project.json"));
const m = config.maintenance;
const version = config.project.version;
const maafw = config.maafw.version;
const python = config.python;
const mode = process.argv[2];
if (
    ![
        "--sync",
        "--check",
        "--ci",
    ].includes(mode)
)
    throw new Error("Use --sync, --check or --ci");
if (!/^\d+\.\d+\.\d+(?:-[\w.-]+)?$/.test(version) || !/^\d+\.\d+\.\d+$/.test(maafw)) {
    throw new Error("Project and MaaFramework versions must be exact versions");
}
for (const value of [
    m.pythonRuntime.windows,
    m.pythonRuntime.standalone,
]) {
    if (!value.startsWith(python.recommendedPython + "."))
        throw new Error("Python runtime minor must match recommendedPython");
}
if (mode === "--ci") {
    const a = m.android;
    const values = {
        python: python.recommendedPython,
        node: m.node,
        PROJECT_VERSION: version,
        MAAFW_VERSION: maafw,
        ANDROID_APP_REPOSITORY: a.appRepository,
        ANDROID_APP_REF: a.appRef,
        ANDROID_AGENT_CORE_REPOSITORY: a.agentCoreRepository,
        ANDROID_AGENT_CORE_TAG: a.agentCoreTag,
        ANDROID_AGENT_PYTHON: a.agentPython,
        ANDROID_NDK: a.ndk,
        ANDROID_PYTHON: a.buildPython,
        JAVA_VERSION: a.java,
        ANDROID_CMAKE: a.cmake,
        ANDROID_SDK: a.sdk,
        // SDK package IDs may include a minor version even when compileSdk is an integer.
        ANDROID_SDK_PLATFORM: a.sdkPlatform,
        ANDROID_BUILD_TOOLS: a.buildTools,
        RCEDIT_VERSION: m.rcedit,
        RCEDIT_SHA256: m.rceditSha256,
    };
    const lines = Object.entries(values)
        .map(
            ([
                key,
                value,
            ]) => {
                if (typeof value !== "string" || /[\r\n]/.test(value)) throw new Error(`Invalid version field: ${key}`);
                return `${key}=${value}\n`;
            },
        )
        .join("");
    appendFileSync(process.env.GITHUB_OUTPUT, lines);
    appendFileSync(process.env.GITHUB_ENV, lines);
} else {
    const drift = [];
    function update(path, expected) {
        if (read(path) === expected) return;
        if (mode === "--sync") writeFileSync(path, expected);
        else drift.push(path);
    }
    function replace(path, changes) {
        let value = read(path);
        for (const [
            pattern,
            replacement,
        ] of changes) {
            if (!pattern.test(value)) throw new Error(`Expected version field missing in ${path}: ${pattern}`);
            value = value.replace(pattern, replacement);
        }
        update(path, value);
    }
    replace("package.json", [
        [
            /"version": "[^"]+"/,
            `"version": "${version}"`,
        ],
        [
            /"node": "[^"]+"/,
            `"node": ">=${m.nodeMinimum}"`,
        ],
        [
            /"packageManager": "[^"]+"/,
            `"packageManager": "yarn@${m.yarn}"`,
        ],
        [
            /"create-maa-project": "[^"]+"/,
            `"create-maa-project": "${m.cmp}"`,
        ],
    ]);
    replace("interface.json", [
        [
            /"version": "[^"]+"/,
            `"version": "v${version}"`,
        ],
    ]);
    // 只更新本次日志的首行版号，保留日期、正文及可能存在的历史记录。
    replace("resource/Changelog.md", [
        [
            /^# v\d+\.\d+\.\d+(?:-[\w.-]+)?(?=[ \t]*(?:\n|$))/,
            `# v${version}`,
        ],
    ]);
    for (const path of [
        "locales/interface_zh.json",
        "locales/interface_en.json",
    ]) {
        replace(path, [
            [
                /("project_title"\s*:\s*"[^"\r\n]*? )v\d+\.\d+\.\d+(?:-[\w.-]+)?(?= - MFAA\b)/,
                (_, prefix) => `${prefix}v${version}`,
            ],
        ]);
    }
    replace("pyproject.toml", [
        [
            /^version = "[^"]+"/m,
            `version = "${version}"`,
        ],
        [
            /^requires-python = "[^"]+"/m,
            `requires-python = "${python.requiresPython}"`,
        ],
        [
            /maafw==[^"\s]+/,
            `maafw==${maafw}`,
        ],
        [
            /target-version = "[^"]+"/,
            `target-version = "py${python.recommendedPython.replace(".", "")}"`,
        ],
        [
            /pythonVersion = "[^"]+"/,
            `pythonVersion = "${python.recommendedPython}"`,
        ],
    ]);
    update(".python-version", python.recommendedPython + "\n");
    update(".node-version", m.node + "\n");
    replace("requirements.in", [
        [
            /maafw==[^\s]+/,
            `maafw==${maafw}`,
        ],
    ]);
    replace("tools/ci/requirements-android.txt", [
        [
            /maafw==[^\s]+/,
            `maafw==${maafw}`,
        ],
    ]);
    function uv(args, capture = false) {
        const result = spawnSync("uv", args, {
            encoding: "utf8",
            stdio: capture
                ? [
                      "ignore",
                      "pipe",
                      "inherit",
                  ]
                : "inherit",
        });
        if (result.error || result.status !== 0)
            throw new Error(`uv ${args[0]} failed; install uv and run yarn versions:sync`);
        return result.stdout;
    }
    if (mode === "--sync") {
        uv(["lock"]);
        uv([
            "export",
            "--locked",
            "--no-dev",
            "--no-emit-project",
            "--no-hashes",
            "--no-header",
            "--format",
            "requirements-txt",
            "--output-file",
            "requirements.txt",
        ]);
        if (!read("yarn.lock").includes(`create-maa-project@${m.cmp}:`)) {
            const yarnEntry = process.env.npm_execpath;
            const result = yarnEntry
                ? spawnSync(
                      process.execPath,
                      [
                          yarnEntry,
                          "install",
                          "--ignore-scripts",
                          "--non-interactive",
                      ],
                      {stdio: "inherit"},
                  )
                : spawnSync(
                      "yarn",
                      [
                          "install",
                          "--ignore-scripts",
                          "--non-interactive",
                      ],
                      {stdio: "inherit", shell: process.platform === "win32"},
                  );
            if (result.error || result.status !== 0) throw new Error("Run yarn install to update yarn.lock");
        }
        console.log("Version files and lockfiles synchronized.");
    } else {
        if (drift.length) throw new Error(`Run yarn versions:sync: ${drift.join(", ")}`);
        if (!read("yarn.lock").includes(`create-maa-project@${m.cmp}:`))
            throw new Error("CMP lockfile is stale; run yarn versions:sync");
        uv([
            "lock",
            "--check",
            "--offline",
        ]);
        const expected = uv(
            [
                "export",
                "--frozen",
                "--offline",
                "--no-dev",
                "--no-emit-project",
                "--no-hashes",
                "--no-header",
                "--format",
                "requirements-txt",
            ],
            true,
        );
        if (read("requirements.txt") !== expected.replaceAll("\r\n", "\n"))
            throw new Error("requirements.txt is stale; run yarn versions:sync");
        console.log("Version declarations and Python lock/export are consistent.");
    }
}
