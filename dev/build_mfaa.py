import os
import sys
import subprocess
import shutil

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
parent_dir = os.path.dirname(current_dir)
os.chdir(parent_dir)

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


def copy_files():
    # 确保目标目录存在
    os.makedirs("MFAAvalonia/Resource", exist_ok=True)
    os.makedirs("MFAAvalonia", exist_ok=True)

    try:
        # 先删除目标目录中的现有文件
        if os.path.exists("MFAAvalonia/interface.json"):
            os.remove("MFAAvalonia/interface.json")

        # 清空Resource目录
        if os.path.exists("MFAAvalonia/Resource"):
            for item in os.listdir("MFAAvalonia/Resource"):
                item_path = os.path.join("MFAAvalonia/Resource", item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)

        # 删除debug目录
        if os.path.exists("MFAAvalonia/debug"):
            shutil.rmtree("MFAAvalonia/debug")

        # 删除logs目录
        if os.path.exists("MFAAvalonia/logs"):
            shutil.rmtree("MFAAvalonia/logs")

        # 删除agent目录
        if os.path.exists("MFAAvalonia/agent"):
            shutil.rmtree("MFAAvalonia/agent")

        # 删除Resource中的descs目录
        if os.path.exists("MFAAvalonia/Resource/descs"):
            shutil.rmtree("MFAAvalonia/Resource/descs")

        # 复制interface.json
        if os.path.exists("assets/interface.json"):
            shutil.copy2("assets/interface.json", "MFAAvalonia/")
        else:
            print("警告: assets/interface.json 不存在")

        # 复制resource文件夹内容
        if os.path.exists("assets/resource"):
            for item in os.listdir("assets/resource"):
                src = os.path.join("assets/resource", item)
                dst = os.path.join("MFAAvalonia/Resource", item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
        else:
            print("警告: assets/resource 文件夹不存在")

        # 复制agent文件夹
        if os.path.exists("agent"):
            shutil.copytree("agent", "MFAAvalonia/agent", dirs_exist_ok=True)

            # 修改main.py文件
            main_py_path = "MFAAvalonia/agent/main.py"
            if os.path.exists(main_py_path):
                with open(main_py_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # 删除check_and_install_dependencies()调用
                content = content.replace("check_and_install_dependencies()", "pass")

                with open(main_py_path, "w", encoding="utf-8") as f:
                    f.write(content)
        else:
            print("警告: agent 文件夹不存在")

        # 复制descs文件夹到Resource目录下
        if os.path.exists("descs"):
            shutil.copytree("descs", "MFAAvalonia/Resource/descs", dirs_exist_ok=True)
        else:
            print("警告: descs 文件夹不存在")

        # 打开MFAAvalonia.exe
        exe_path = "MFAAvalonia/MFAAvalonia.exe"
        if os.path.exists(exe_path):
            subprocess.Popen(exe_path)
            print("MFAAvalonia 程序构建成功！")
        else:
            print(f"错误: {exe_path} 不存在")

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    copy_files()
