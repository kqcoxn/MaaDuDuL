#!/usr/bin/env node

"use strict";

const {spawnSync} = require("node:child_process");
const {platform} = require("node:os");
const {existsSync, readFileSync} = require("node:fs");
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
const project = JSON.parse(readFileSync(resolve(__dirname, "..", "..", "maa-project.json"), "utf8"));
const probe = spawnSync(
    python,
    [
        "-c",
        "import sys, importlib.metadata as m; import re, operator; ops = {'>=':operator.ge, '<=':operator.le, '>':operator.gt, '<':operator.lt, '==':operator.eq}; bounds = [re.fullmatch(r'(>=|<=|>|<|==)([0-9.]+)', x.strip()) for x in sys.argv[2].split(',')]; assert all(b and ops[b[1]](sys.version_info[:len(b[2].split('.'))], tuple(map(int,b[2].split('.')))) for b in bounds), 'Python does not match maa-project.json python.requiresPython'; assert m.version('maafw') == sys.argv[1], 'Run uv sync --frozen: maafw version mismatch'",
        project.maafw.version,
        project.python.requiresPython,
    ],
    {
        stdio: "inherit",
        windowsHide: true,
    },
);
if (probe.error || probe.status !== 0) {
    console.error("Python environment validation failed. Run uv sync --frozen.");
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
