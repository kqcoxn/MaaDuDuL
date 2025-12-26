#!/bin/bash
# 嵌入式Python安装脚本（Unix平台：macOS/Linux）

set -e  # 遇到错误立即退出

# 基本变量
PYTHON_VERSION="3.12.7"
DEST_DIR="install/python"
SCRIPTS_DIR="ci"

# 检测操作系统和架构
OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

echo -e "\033[36m检测到操作系统: $OS_TYPE\033[0m"
echo -e "\033[36m检测到架构: $ARCH_TYPE\033[0m"

# 根据架构映射下载URL所需的架构标识
case "$ARCH_TYPE" in
    x86_64|amd64)
        ARCH="x86_64"
        ;;
    aarch64|arm64)
        ARCH="aarch64"
        ;;
    *)
        echo -e "\033[31m错误: 不支持的架构 $ARCH_TYPE\033[0m"
        exit 1
        ;;
esac

# 根据操作系统设置下载URL
case "$OS_TYPE" in
    Darwin)
        # macOS平台使用python-build-standalone
        if [ "$ARCH" = "x86_64" ]; then
            PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-${PYTHON_VERSION}+20241016-x86_64-apple-darwin-install_only.tar.gz"
        else
            PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-${PYTHON_VERSION}+20241016-aarch64-apple-darwin-install_only.tar.gz"
        fi
        USE_TAR=true
        ;;
    Linux)
        # Linux平台使用预编译的Python独立构建
        PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-${PYTHON_VERSION}+20241016-${ARCH}-unknown-linux-gnu-install_only.tar.gz"
        USE_TAR=true
        ;;
    *)
        echo -e "\033[31m错误: 不支持的操作系统 $OS_TYPE\033[0m"
        exit 1
        ;;
esac

# 创建目标目录
mkdir -p "$DEST_DIR"
echo -e "\033[36m创建目录: $DEST_DIR\033[0m"

# 检查Python是否已经存在
PYTHON_BIN="$DEST_DIR/bin/python3"
if [ -f "$PYTHON_BIN" ]; then
    echo -e "\033[33mPython已存在于 $DEST_DIR，跳过安装。\033[0m"
    exit 0
fi

# 下载并安装Python
if [ "$USE_TAR" = true ]; then
    # tar.gz安装方式（适用于macOS和Linux）
    PYTHON_TAR="python-embedded.tar.gz"
    echo -e "\033[36m下载Python: $PYTHON_URL\033[0m"
    curl -L -o "$PYTHON_TAR" "$PYTHON_URL"
    
    # 解压Python
    echo -e "\033[36m解压Python到: $DEST_DIR\033[0m"
    tar -xzf "$PYTHON_TAR" -C "$DEST_DIR" --strip-components=1
    rm "$PYTHON_TAR"
    echo -e "\033[32mPython已解压到 $DEST_DIR\033[0m"
fi

# 确保Python可执行（使用绝对路径避免cd后路径失效）
BASE_DIR=$(pwd)
if [ -f "$DEST_DIR/bin/python3" ]; then
    chmod +x "$DEST_DIR/bin/python3"
    PYTHON_BIN="$BASE_DIR/$DEST_DIR/bin/python3"
elif [ -f "$DEST_DIR/bin/python" ]; then
    chmod +x "$DEST_DIR/bin/python"
    PYTHON_BIN="$BASE_DIR/$DEST_DIR/bin/python"
else
    echo -e "\033[31m错误: 未找到Python可执行文件\033[0m"
    exit 1
fi

# 复制setup_pip.py脚本
SETUP_PIP_SOURCE="$SCRIPTS_DIR/setup_pip.py"
SETUP_PIP_DEST="$DEST_DIR/setup_pip.py"

if [ -f "$SETUP_PIP_SOURCE" ]; then
    echo -e "\033[36m复制脚本...\033[0m"
    cp "$SETUP_PIP_SOURCE" "$SETUP_PIP_DEST"
else
    echo -e "\033[31m错误: 未找到 $SETUP_PIP_SOURCE\033[0m"
    exit 1
fi

# 检查pip是否已安装
echo -e "\033[36m检查pip安装状态...\033[0m"
cd "$DEST_DIR"

if $PYTHON_BIN -m pip --version > /dev/null 2>&1; then
    echo -e "\033[33mpip已安装，版本: $($PYTHON_BIN -m pip --version)\033[0m"
else
    echo -e "\033[36m安装pip...\033[0m"
    $PYTHON_BIN setup_pip.py
    echo -e "\033[32mpip已安装\033[0m"
fi

cd - > /dev/null

# 清理临时文件
echo -e "\033[36m清理临时文件...\033[0m"
if [ -f "$DEST_DIR/setup_pip.py" ]; then
    rm "$DEST_DIR/setup_pip.py"
    echo -e "\033[32m已清理 setup_pip.py\033[0m"
fi

# 确保压缩包已清理
if [ -f "python-embedded.tar.gz" ]; then
    rm "python-embedded.tar.gz"
    echo -e "\033[32m已清理 Python 压缩包\033[0m"
fi

echo -e "\033[32m全部完成\033[0m"
