#!/bin/bash
# 嵌入式Python安装脚本（Unix平台：macOS/Linux）

set -e  # 遇到错误立即退出

# 基本变量
PYTHON_VERSION="3.12.9"
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
        # macOS平台
        if [ "$ARCH" = "x86_64" ]; then
            PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.pkg"
            USE_PKG=true
        else
            PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-macos11.pkg"
            USE_PKG=true
        fi
        ;;
    Linux)
        # Linux平台使用预编译的Python独立构建
        PYTHON_URL="https://github.com/indygreg/python-build-standalone/releases/download/20241016/cpython-${PYTHON_VERSION}+20241016-${ARCH}-unknown-linux-gnu-install_only.tar.gz"
        USE_PKG=false
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
if [ "$USE_PKG" = true ]; then
    # macOS pkg安装方式
    PYTHON_PKG="python-installer.pkg"
    echo -e "\033[36m下载Python pkg: $PYTHON_URL\033[0m"
    curl -L -o "$PYTHON_PKG" "$PYTHON_URL"
    
    # 提取pkg内容到临时目录
    TEMP_DIR=$(mktemp -d)
    echo -e "\033[36m提取pkg到临时目录...\033[0m"
    
    # macOS上，从官方pkg提取Python框架
    # 使用pkgutil展开pkg
    pkgutil --expand "$PYTHON_PKG" "$TEMP_DIR/expanded"
    
    # 查找Python框架的Payload并提取
    FRAMEWORK_PAYLOAD=$(find "$TEMP_DIR/expanded" -name "Payload" -path "*/Python.framework/*" | head -n 1)
    if [ -n "$FRAMEWORK_PAYLOAD" ]; then
        cd "$TEMP_DIR"
        cat "$FRAMEWORK_PAYLOAD" | gunzip -dc | cpio -i
        
        # 查找实际的Python安装位置
        PYTHON_FW_PATH=$(find "$TEMP_DIR" -type d -name "Python.framework" | head -n 1)
        if [ -n "$PYTHON_FW_PATH" ]; then
            # 获取版本号（主版本.次版本）
            PYTHON_VER_SHORT=$(echo "$PYTHON_VERSION" | cut -d. -f1,2)
            PYTHON_INSTALL_PATH="$PYTHON_FW_PATH/Versions/$PYTHON_VER_SHORT"
            
            if [ -d "$PYTHON_INSTALL_PATH" ]; then
                # 复制到目标目录
                cp -r "$PYTHON_INSTALL_PATH/"* "$DEST_DIR/"
                echo -e "\033[32mPython框架已提取到 $DEST_DIR\033[0m"
            fi
        fi
        cd - > /dev/null
    fi
    
    # 清理
    rm -rf "$TEMP_DIR" "$PYTHON_PKG"
else
    # Linux tar.gz安装方式
    PYTHON_TAR="python-embedded.tar.gz"
    echo -e "\033[36m下载Python: $PYTHON_URL\033[0m"
    curl -L -o "$PYTHON_TAR" "$PYTHON_URL"
    
    # 解压Python
    echo -e "\033[36m解压Python到: $DEST_DIR\033[0m"
    tar -xzf "$PYTHON_TAR" -C "$DEST_DIR" --strip-components=1
    rm "$PYTHON_TAR"
fi

# 确保Python可执行
if [ -f "$DEST_DIR/bin/python3" ]; then
    chmod +x "$DEST_DIR/bin/python3"
    PYTHON_BIN="$DEST_DIR/bin/python3"
elif [ -f "$DEST_DIR/bin/python" ]; then
    chmod +x "$DEST_DIR/bin/python"
    PYTHON_BIN="$DEST_DIR/bin/python"
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

echo -e "\033[32m全部完成\033[0m"
