# 参与开发

## 少量 JSON 文件修改

如果您只是想改一点点 JSON 文件/文档等，可以参考：[牛牛也能看懂的 GitHub Pull Request 使用指南](https://maa.plus/docs/zh-cn/develop/pr-tutorial.html)

## 深度参与开发

如果您打算大量修改内容、解决某个 issue 或有新想法，可以在交流群内与开发组确认没有人正在处理该 issue，并在简单交流想法后按如下方式开始尝试开发：

1. 打开 MDDL 主仓库，点击 Fork，继续点击 Create fork
2. 克隆你自己的仓库到本地，并拉取子模块：
   ```bash
   git clone --recursive https://github.com/<your_username>/MaaNewMoonAccompanying.git
   ```
3. 下载 MaaFramework 的最新稳定版 [Release](https://github.com/MaaXYZ/MaaFramework/releases) 包，解压到 `/deps` 文件夹中。
4. 配置编程环境
   1. 推荐使用 vscode 作为 IDE
   2. 在根目录对应文件夹中配置并快速启动相关工具：
      - `/MFAAvalonia`：[MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia/releases)，本地 GUI 测试，可以使用 `yarn dev` 快速配置文件并运行
      - `/MFATools`：[MFATools](https://github.com/SweetSmellFox/MFATools/releases)，截图、roi 测绘小工具，可以使用 `yarn tool` 快速运行
   3. 配置本地环境：
      - 安装 python `3.12.9` 版本
      - 安装相关依赖包：
        ```shell
        pip install maafw maadebugger
        ```
5. 使用 MaaDebugger 进行调试：
   ```shell
   yarn debug
   ```
6. 增删改代码（项目目录说明详见下一节）
7. 提交 PR
