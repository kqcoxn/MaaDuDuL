#!/usr/bin/env node

"use strict";

const { spawnSync } = require("node:child_process");
const { platform } = require("node:os");

const scriptArgs = process.argv.slice(2);

if (scriptArgs.length === 0) {
    console.error("Usage: node dev/run_python.js <script> [args ...]");
    process.exit(2);
}

const configuredPython = process.env.MDDL_PYTHON;
const defaultCandidates =
    platform() === "win32" ? ["python", "py"] : ["python3", "python"];
const candidates = configuredPython
    ? [configuredPython]
    : defaultCandidates;

function canRun(executable) {
    const result = spawnSync(executable, ["--version"], {
        stdio: "ignore",
        windowsHide: true,
    });
    return !result.error && result.status === 0;
}

const python = candidates.find(canRun);

if (!python) {
    const hint = configuredPython
        ? `MDDL_PYTHON=${configuredPython}`
        : "python3/python";
    console.error(`Unable to find a usable Python interpreter (${hint}).`);
    process.exit(1);
}

const result = spawnSync(python, scriptArgs, {
    stdio: "inherit",
    windowsHide: true,
});

if (result.error) {
    console.error(`Failed to start Python: ${result.error.message}`);
    process.exit(1);
}

process.exit(result.status === null ? 1 : result.status);
