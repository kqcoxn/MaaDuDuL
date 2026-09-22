"""Check the signed APK, embedded runtimes and published upgrade identity."""

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

ABIS = {"arm64-v8a", "x86_64"}
ROOT = Path(__file__).resolve().parents[3]


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def check_upgrade(current: dict) -> None:
    repository = os.environ["GITHUB_REPOSITORY"]
    releases = json.loads(run("gh", "api", f"repos/{repository}/releases?per_page=100"))
    # The old client published one APK per ABI; the new client publishes a universal APK.
    # Check the newest available baseline of each shape so the migration covers both old ABIs.
    found = set()
    for release in releases:
        if release["draft"] or release["tag_name"] == os.environ["GITHUB_REF_NAME"]:
            continue
        for asset in release["assets"]:
            for arch in ("universal", "arm64", "x64"):
                if arch in found or not asset["name"].endswith(f"-android-{arch}.build-info.json"):
                    continue
                previous = json.loads(
                    run(
                        "gh",
                        "api",
                        f"repos/{repository}/releases/assets/{asset['id']}",
                        "-H",
                        "Accept: application/octet-stream",
                    )
                )
                for key in ("application_id", "signing_certificate_sha256"):
                    require(previous.get(key) == current[key], f"Android upgrade identity changed: {key}")
                previous_abis = set(previous.get("abis", [previous.get("abi")]))
                require(bool(previous_abis) and previous_abis <= ABIS, "Previous APK ABIs are missing or unsupported")
                require(current["version_code"] > int(previous["version_code"]), "APK versionCode must increase")
                found.add(arch)
    if not found:
        print("::warning::No published Android build-info baseline; device upgrade remains unverified.")
    else:
        print(f"Upgrade identity verified against: {', '.join(sorted(found))}")


def main() -> None:
    env = os.environ
    config = json.loads((ROOT / "maa-project.json").read_text(encoding="utf-8"))
    android = config["maintenance"]["android"]
    workspace = Path(env["GITHUB_WORKSPACE"])
    app = workspace / "app-source"
    apks = list((app / "app/build/outputs/apk/release").glob("*.apk"))
    require(len(apks) == 1, f"Expected one universal APK, found {apks}")
    apk = apks[0]
    build_tools = Path(env["ANDROID_HOME"]) / "build-tools" / android["buildTools"]
    run(str(build_tools / "zipalign"), "-c", "-P", "16", "4", str(apk))
    signature = run(str(build_tools / "apksigner"), "verify", "--verbose", "--print-certs", str(apk))
    digests = re.findall(r"^Signer #\d+ certificate SHA-256 digest: ([0-9a-fA-F]+)$", signature, re.M)
    require(len(digests) == 1 and digests[0].lower() == env["SIGNING_SHA256"], "APK signing certificate mismatch")
    badging = run(str(build_tools / "aapt2"), "dump", "badging", str(apk))
    package = re.search(r"^package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'", badging, re.M)
    require(package is not None, f"Cannot read APK package metadata:\n{badging}")
    require(
        package.groups() == (env["APPLICATION_ID"], env["VERSION_CODE"], env["BUILD_VERSION_NAME"]),
        f"Unexpected APK identity: {package.group(0)}",
    )
    minimum = re.search(r"^(?:minSdkVersion|sdkVersion):'(\d+)'", badging, re.M)
    require(minimum is not None and minimum[1] == "28", f"Expected minimum SDK 28:\n{badging}")
    require("application-debuggable" not in badging, "Release APK is debuggable")
    require("launchable-activity:" in badging, "APK has no launcher activity")
    require("application-label:'MaaDuDuL'" in badging, "APK launcher label is missing")
    require(re.search(r"^application: .*icon='[^']+'", badging, re.M) is not None, "APK icon is missing")

    with zipfile.ZipFile(apk) as package_zip:
        names = set(package_zip.namelist())
        require(
            {name.split("/")[1] for name in names if name.startswith("lib/") and name.endswith(".so")} == ABIS,
            "Wrong APK ABIs",
        )
        for abi in ABIS:
            for library in (
                "libMaaFramework.so",
                "libMaaAgentClient.so",
                "libMaaAgentServer.so",
                "libMaaAndroidNativeControlUnit.so",
            ):
                require(f"lib/{abi}/{library}" in names, f"Missing native library: {abi}/{library}")
        with zipfile.ZipFile(io.BytesIO(package_zip.read("assets/pi.zip"))) as payload:
            for filename in (
                "interface.json",
                "agent/main.py",
                "public/logo.png",
                "locales/interface_zh.json",
                "LICENSE",
                "resource/base/model/ocr/det.onnx",
                "resource/base/model/ocr/rec.onnx",
                "resource/base/model/ocr/keys.txt",
            ):
                require(filename in payload.namelist(), f"Missing resource payload: {filename}")
            interface = json.loads(payload.read("interface.json"))
            require(interface["version"] == env["BUILD_VERSION_NAME"], "Resource version differs from APK")
            for imported in interface.get("import", []):
                require(imported in payload.namelist(), f"Missing Interface import: {imported}")
        descriptor = json.loads(package_zip.read("assets/agent/agent-runtime.json"))
        require(len(descriptor["runtimes"]) == 1, "Expected one Python agent runtime")
        runtime = descriptor["runtimes"][0]
        require(
            runtime["executable"] == "bin/python3" and runtime["args"] == ["-u", "agent/main.py"],
            "Agent launch command does not match the project",
        )
        with zipfile.ZipFile(io.BytesIO(package_zip.read("assets/agent/bundle.zip"))) as bundles:
            for abi in ABIS:
                require(f"{abi}/bin/python3" in bundles.namelist(), f"Missing Python interpreter: {abi}")
                core = json.loads(bundles.read(f"{abi}/agent-core.json"))
                require(core["provides"]["maafw"] == config["maafw"]["version"], "Agent binding version drift")
                require(core["python"] == android["agentPython"], "Agent Python version drift")
                with zipfile.ZipFile(io.BytesIO(bundles.read(f"{abi}/site-packages/pure.zip"))) as pure:
                    require("maa/agent/agent_server.py" in pure.namelist(), "Maa agent binding missing")
                    require(b'platform_type == "android"' in pure.read("maa/library.py"), "Android loader missing")

    info = {
        "application_id": env["APPLICATION_ID"],
        "display_version": env["BUILD_VERSION_NAME"],
        "version_code": int(env["VERSION_CODE"]),
        "abis": sorted(ABIS),
        "signing_certificate_sha256": env["SIGNING_SHA256"],
        "resource_commit": env["GITHUB_SHA"],
        "app_repository": android["appRepository"],
        "app_ref": android["appRef"],
        "app_commit": run("git", "-C", str(app), "rev-parse", "HEAD").strip(),
        "agent_core_repository": android["agentCoreRepository"],
        "agent_core_tag": android["agentCoreTag"],
        "agent_python": android["agentPython"],
        "maafw_runtime_version": config["maafw"]["version"],
        "maafw_python_ref": f"v{config['maafw']['version']}",
        "workflow_run_id": env["GITHUB_RUN_ID"],
    }
    check_upgrade(info)
    output = workspace / "android-artifacts"
    output.mkdir(exist_ok=True)
    name = env["ARTIFACT_NAME"]
    destination = output / f"{name}.apk"
    shutil.copy2(apk, destination)
    with destination.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    (output / f"{name}.apk.sha256").write_text(f"{digest}  {name}.apk\n", encoding="utf-8")
    (output / f"{name}.build-info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    print(f"Verified Android APK: {destination}")


if __name__ == "__main__":
    main()
