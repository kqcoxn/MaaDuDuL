#!/usr/bin/env node

"use strict";

const {spawnSync} = require("node:child_process");
const {platform} = require("node:os");
const {existsSync} = require("node:fs");
const {resolve} = require("node:path");

const scriptArgs = process.argv.slice(2);

if (scriptArgs.length === 0) {
    console.error("Usage: node tools/dev/run_python.js <script> [args ...]");
    process.exit(2);
}

const configuredPython = process.env.MDDL_PYTHON;
const projectPython = resolve(
    __dirname,
    "..",
    "..",
    ".venv",
    platform() === "win32" ? "Scripts/python.exe" : "bin/python",
);
// Keep the virtualenv executable path: realpath would bypass POSIX venvs.
const python = configuredPython ? resolve(configuredPython) : projectPython;
if (!existsSync(python)) {
    console.error(
        `Python environment missing: ${python}. Run uv sync --frozen, or set MDDL_PYTHON to an executable path.`,
    );
    process.exit(1);
}
const probe = spawnSync(
    python,
    ["-B", resolve(__dirname, "..", "..", "agent", "dev_environment.py")],
    {
        stdio: "inherit",
        windowsHide: true,
    },
);
if (probe.error || probe.status !== 0) {
    if (probe.error) {
        console.error(`Failed to check Python environment: ${probe.error.message}`);
    }
    process.exit(1);
}

const result = spawnSync(python, scriptArgs, {
    stdio: "inherit",
    windowsHide: true,
    cwd: resolve(__dirname, "..", ".."),
});

if (result.error) {
    console.error(`Failed to start Python: ${result.error.message}`);
    process.exit(1);
}

process.exit(result.status === null ? 1 : result.status);
