# 参与开发

## 少量 JSON 文件修改

如果您只是想改一点点 JSON 文件/文档等，可以参考：[牛牛也能看懂的 GitHub Pull Request 使用指南](https://maa.plus/docs/zh-cn/develop/pr-tutorial.html)

## 深度参与开发

如果您打算大量修改内容、解决某个 issue 或有新想法，可以在交流群内与开发组确认没有人正在处理该 issue，并在简单交流想法后按如下方式开始尝试开发：

1. 打开 MDDL 主仓库，点击 Fork，继续点击 Create fork
2. 克隆你自己的仓库到本地，并拉取子模块：
   ```bash
   git clone --recursive https://github.com/<your_username>/MaaDuDuL.git
   ```
3. 安装 Node.js 22.13+、Yarn 1.22.22 和 uv。运行 `yarn install --frozen-lockfile`、`uv sync --frozen`，再运行 `uv run python tools/configure.py` 从子模块准备 OCR。
4. 配置编程环境
   1. 推荐使用 vscode 作为 IDE
   2. 在根目录对应文件夹中配置并快速启动相关工具：
      - `/MFAAvalonia`：[MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia/releases)，本地 GUI 测试，可以使用 `yarn dev` 快速配置文件并运行
      - `/MFATools`：[MFATools](https://github.com/SweetSmellFox/MFATools/releases)，截图、roi 测绘小工具，可以使用 `yarn tool` 快速运行
   3. 配置本地环境：
      - `uv sync --frozen` 使用项目锁定的 Python 和依赖，开发命令会优先使用 `.venv`。
      - 使用 `yarn run check` 执行静态检查；架构维护见仓库 `tools/docs/template-migration.md`。
5. 使用 MaaDebugger 进行调试：
   ```shell
   yarn debug
   ```

   根目录的开发命令已按当前系统自动选择 Python 与 MFAAvalonia 可执行文件，Windows、macOS、Linux 均使用同一套命令。若系统未将 Python 命令加入 PATH，可通过 `MDDL_PYTHON` 指定解释器路径。
6. 增删改代码（项目目录说明详见下一节）
7. 提交 PR
