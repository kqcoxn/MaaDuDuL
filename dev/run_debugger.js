#!/usr/bin/env node

"use strict";

const { spawnSync } = require("node:child_process");
const { existsSync } = require("node:fs");
const { basename, resolve } = require("node:path");

const DEBUGGER_PACKAGE =
    process.env.MDDL_DEBUGGER_PACKAGE ||
    "@weinibuliu/maa-debugger@latest";
const args = process.argv.slice(2);

function run(command, commandArgs, options = {}) {
    const result = spawnSync(command, commandArgs, {
        stdio: "inherit",
        windowsHide: true,
        ...options,
    });

    if (result.error) {
        return { status: 1, error: result.error };
    }

    return { status: result.status === null ? 1 : result.status };
}

function runYarn(yarnArgs, options = {}) {
    const yarnEntrypoint = process.env.npm_execpath;
    if (
        yarnEntrypoint &&
        basename(yarnEntrypoint).toLowerCase().includes("yarn")
    ) {
        return run(process.execPath, [yarnEntrypoint, ...yarnArgs], options);
    }

    return run("yarn", yarnArgs, {
        shell: process.platform === "win32",
        ...options,
    });
}

function queryYarn(yarnArgs) {
    const yarnEntrypoint = process.env.npm_execpath;
    const command =
        yarnEntrypoint && basename(yarnEntrypoint).toLowerCase().includes("yarn")
            ? process.execPath
            : "yarn";
    const commandArgs = command === process.execPath
        ? [yarnEntrypoint, ...yarnArgs]
        : yarnArgs;
    return spawnSync(command, commandArgs, {
        encoding: "utf8",
        windowsHide: true,
        shell: command === "yarn" && process.platform === "win32",
    });
}

function getYarnMajorVersion() {
    const result = queryYarn(["--version"]);
    if (result.error || result.status !== 0) {
        return null;
    }

    const majorVersion = Number.parseInt(result.stdout.trim().split(".")[0], 10);
    return Number.isNaN(majorVersion) ? null : majorVersion;
}

function getGlobalDebuggerEntrypoint() {
    const result = queryYarn(["global", "dir"]);
    if (result.error || result.status !== 0) {
        return null;
    }

    const globalDirectory = result.stdout.trim();
    if (!globalDirectory) {
        return null;
    }

    const entrypoint = resolve(
        globalDirectory,
        "node_modules",
        "@weinibuliu",
        "maa-debugger",
        "index.cjs",
    );
    return existsSync(entrypoint) ? entrypoint : null;
}

function getLocalDebuggerEntrypoint() {
    const entrypoint = resolve(
        __dirname,
        "..",
        "node_modules",
        "@weinibuliu",
        "maa-debugger",
        "index.cjs",
    );
    return existsSync(entrypoint) ? entrypoint : null;
}

const localDebugger = getLocalDebuggerEntrypoint();
if (localDebugger) {
    process.exit(run(process.execPath, [localDebugger, ...args]).status);
}

const yarnMajorVersion = getYarnMajorVersion();
if (yarnMajorVersion !== null && yarnMajorVersion >= 2) {
    process.exit(runYarn(["dlx", DEBUGGER_PACKAGE, ...args]).status);
}

const globalDebugger = getGlobalDebuggerEntrypoint();
if (globalDebugger) {
    process.exit(run(process.execPath, [globalDebugger, ...args]).status);
}

const installResult = runYarn(["global", "add", DEBUGGER_PACKAGE]);
if (installResult.status !== 0) {
    console.error(
        "MaaDebugger 安装失败，请检查网络，或手动执行: yarn global add @weinibuliu/maa-debugger@latest",
    );
    process.exit(installResult.status);
}

const installedDebugger = getGlobalDebuggerEntrypoint();
if (!installedDebugger) {
    console.error("MaaDebugger 已安装，但未找到 maa-debugger 命令。");
    process.exit(1);
}

process.exit(run(process.execPath, [installedDebugger, ...args]).status);
