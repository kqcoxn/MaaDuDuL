#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_CREATE_ROOT = path.resolve(
  process.env.MAA_PROJECT_CREATE_ROOT ?? path.join(SCRIPT_DIR, ".."),
);
const UPSTREAM_SKILL = path.join("skills", "create-maa-project", "SKILL.md");
const PACKAGE_NAME = "create-maa-project";
const LATEST_RELEASE_URL =
  "https://github.com/Windsland52/create-maa-project/releases/latest";
const DEFAULT_BRANCH_README_URL =
  "https://raw.githubusercontent.com/Windsland52/create-maa-project/main/README.md";
const DEFAULT_BRANCH_SKILL_URL =
  "https://raw.githubusercontent.com/Windsland52/create-maa-project/main/skills/create-maa-project/SKILL.md";

function parseArgs(argv) {
  const roots = [];
  let ambient = true;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--no-ambient") {
      ambient = false;
      continue;
    }
    if (argument !== "--root" || !argv[index + 1] || argv[index + 1].startsWith("--")) {
      throw new Error(
        "Usage: find-create-maa-project-skill.mjs [--no-ambient] [--root PATH ...]",
      );
    }
    roots.push(path.resolve(argv[index + 1]));
    index += 1;
  }
  return { roots, ambient };
}

function canonical(candidate) {
  try {
    return fs.realpathSync.native(candidate);
  } catch {
    return path.resolve(candidate);
  }
}

function isFile(candidate) {
  try {
    return fs.statSync(candidate).isFile();
  } catch {
    return false;
  }
}

function addCandidate(list, seen, candidate, source, precedence) {
  const resolved = canonical(candidate);
  const key = process.platform === "win32" ? resolved.toLowerCase() : resolved;
  if (seen.has(key)) return;
  seen.add(key);
  list.push({ path: resolved, source, precedence });
}

function ancestors(start) {
  const result = [];
  let current = path.resolve(start);
  while (true) {
    result.push(current);
    const parent = path.dirname(current);
    if (parent === current) return result;
    current = parent;
  }
}

function packageInfo(candidate) {
  const packageJson = path.join(candidate, "package.json");
  if (!isFile(packageJson)) return undefined;
  try {
    const metadata = JSON.parse(fs.readFileSync(packageJson, "utf8"));
    if (metadata.name !== PACKAGE_NAME) return undefined;
    return { root: canonical(candidate), version: metadata.version ?? null };
  } catch {
    return undefined;
  }
}

function runPackageManager(command, args) {
  try {
    const executable = process.platform === "win32" ? `${command}.cmd` : command;
    return execFileSync(executable, args, {
      encoding: "utf8",
      shell: process.platform === "win32",
      stdio: ["ignore", "pipe", "ignore"],
      timeout: 5000,
    });
  } catch {
    return undefined;
  }
}

function globalPackagePaths(manager) {
  if (manager === "npm") {
    const root = runPackageManager(manager, ["root", "-g"])?.trim();
    return root ? [path.join(root, PACKAGE_NAME)] : [];
  }

  const output = runPackageManager(manager, ["list", "-g", "--json", PACKAGE_NAME]);
  if (!output) return [];

  try {
    const report = JSON.parse(output);
    const entries = Array.isArray(report) ? report : [report];
    return entries
      .flatMap((entry) => Object.values(entry.dependencies ?? {}))
      .filter((dependency) => dependency.path)
      .map((dependency) => dependency.path);
  } catch {
    return [];
  }
}

function skillFromExplicitRoot(root) {
  const candidates = [
    root,
    path.join(root, "SKILL.md"),
    path.join(root, "create-maa-project", "SKILL.md"),
    path.join(root, UPSTREAM_SKILL),
  ];
  return candidates.find((candidate) => upstreamSkillInfo(candidate));
}

function upstreamSkillInfo(candidate) {
  if (!isFile(candidate)) return undefined;
  if (
    canonical(candidate).startsWith(`${canonical(PROJECT_CREATE_ROOT)}${path.sep}`)
  ) {
    return undefined;
  }
  try {
    const content = fs.readFileSync(candidate, "utf8");
    const head = content.slice(0, 4096);
    if (!/^---\r?\n[\s\S]*?^name:\s*["']?create-maa-project["']?\s*$/m.test(head)) {
      return undefined;
    }
    const version = head.match(/^version:\s*["']?([^"'\r\n#]+?)["']?\s*$/m)?.[1] ?? null;
    return {
      skillVersion: version,
    };
  } catch {
    return undefined;
  }
}

function emit(result) {
  console.log(
    JSON.stringify(
      {
        versionPolicy: "latest",
        guidanceAuthority: "latest-release",
        latestReleaseUrl: LATEST_RELEASE_URL,
        defaultBranchReadmeUrl: DEFAULT_BRANCH_README_URL,
        defaultBranchSkillUrl: DEFAULT_BRANCH_SKILL_URL,
        ...result,
      },
      null,
      2,
    ),
  );
}

function findSkillCandidate(candidates) {
  candidates.sort((left, right) => left.precedence - right.precedence);
  for (const candidate of candidates) {
    const skill = upstreamSkillInfo(candidate.path);
    if (!skill) continue;
    return {
      status: "found",
      source: candidate.source,
      skillPath: candidate.path,
      packageRoot: null,
      packageVersion: null,
      skillVersion: skill.skillVersion,
    };
  }
  return undefined;
}

function findPackageCandidate(candidates) {
  candidates.sort((left, right) => left.precedence - right.precedence);
  let packageWithoutSkill;
  for (const candidate of candidates) {
    const info = packageInfo(candidate.path);
    if (!info) continue;
    const skillPath = path.join(info.root, UPSTREAM_SKILL);
    const skill = upstreamSkillInfo(skillPath);
    if (skill) {
      return {
        status: "found",
        source: candidate.source,
        skillPath,
        packageRoot: info.root,
        packageVersion: info.version,
        skillVersion: skill.skillVersion,
      };
    }
    packageWithoutSkill ??= { source: candidate.source, info };
  }
  if (packageWithoutSkill) {
    return {
      status: "package-without-skill",
      source: packageWithoutSkill.source,
      skillPath: null,
      packageRoot: packageWithoutSkill.info.root,
      packageVersion: packageWithoutSkill.info.version,
      skillVersion: null,
    };
  }
  return undefined;
}

function main() {
  const { roots: explicitRoots, ambient } = parseArgs(process.argv.slice(2));
  const skillCandidates = [];
  const packageCandidates = [];
  const seenSkills = new Set();
  const seenPackages = new Set();

  for (const root of explicitRoots) {
    if (packageInfo(root)) {
      addCandidate(packageCandidates, seenPackages, root, "explicit-package", 0);
      continue;
    }

    const skill = skillFromExplicitRoot(root);
    if (skill) addCandidate(skillCandidates, seenSkills, skill, "explicit", 0);
    const packageRoot = path.dirname(root);
    if (packageInfo(packageRoot)) {
      addCandidate(packageCandidates, seenPackages, packageRoot, "explicit-package", 0);
    }
  }

  const explicitSkill = findSkillCandidate(skillCandidates);
  if (explicitSkill) {
    emit(explicitSkill);
    return;
  }

  const explicitPackage = findPackageCandidate(packageCandidates);
  if (explicitPackage) {
    emit(explicitPackage);
    return;
  }
  if (!ambient) {
    emit({
      status: "not-found",
      source: null,
      skillPath: null,
      packageRoot: null,
      packageVersion: null,
      skillVersion: null,
    });
    return;
  }

  const home = os.homedir();
  const projectRoots = ancestors(process.cwd());
  const skillRoots = [];
  for (const root of projectRoots) {
    skillRoots.push(
      path.join(root, ".codex", "skills"),
      path.join(root, ".agents", "skills"),
      path.join(root, ".claude", "skills"),
    );
  }
  if (process.env.CODEX_HOME) {
    skillRoots.push(path.join(process.env.CODEX_HOME, "skills"));
  }
  skillRoots.push(
    path.join(home, ".codex", "skills"),
    path.join(home, ".agents", "skills"),
    path.join(home, ".claude", "skills"),
  );

  for (const root of skillRoots) {
    addCandidate(
      skillCandidates,
      seenSkills,
      path.join(root, "create-maa-project", "SKILL.md"),
      "installed-skill",
      1,
    );
  }
  for (const root of projectRoots) {
    addCandidate(
      packageCandidates,
      seenPackages,
      path.join(root, "node_modules", PACKAGE_NAME),
      "project-package",
      2,
    );
  }
  for (const manager of ["npm", "pnpm"]) {
    for (const root of globalPackagePaths(manager)) {
      addCandidate(packageCandidates, seenPackages, root, `${manager}-global-package`, 3);
    }
  }

  const ambientSkill = findSkillCandidate(skillCandidates);
  if (ambientSkill) {
    emit(ambientSkill);
    return;
  }

  const ambientPackage = findPackageCandidate(packageCandidates);
  if (ambientPackage) {
    emit(ambientPackage);
    return;
  }

  emit({
    status: "not-found",
    source: null,
    skillPath: null,
    packageRoot: null,
    packageVersion: null,
    skillVersion: null,
  });
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
}
