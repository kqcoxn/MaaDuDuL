import {readFileSync} from "node:fs";
const project = JSON.parse(readFileSync(new URL("./maa-project.json", import.meta.url), "utf8"));

export default {
    cwd: import.meta.dirname,
    maaVersion: project.maafw.version,
    interfacePath: "interface.json",
    check: {},
    vscode: {
        agents: {
            uv: "Maa Agent: Debug",
        },
    },
};
