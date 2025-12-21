from pathlib import Path
import json
import sys
import io
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

working_dir = Path(__file__).parent.parent
resource_path = working_dir / "assets" / "resource"
pipeline_paths = [
    (file / "pipeline") for file in resource_path.iterdir() if file.is_dir()
]


def merge_json_files(pipeline_dir):
    """合并pipeline目录下所有.json文件到nodes.json"""
    if not pipeline_dir.exists():
        return

    merged_data = {}

    # 递归遍历所有.json文件
    def collect_json(directory):
        for item in directory.iterdir():
            if item.is_dir():
                collect_json(item)
            elif item.suffix == ".json":
                try:
                    with open(item, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 将当前文件的内容合并到merged_data中
                        if isinstance(data, dict):
                            merged_data.update(data)
                        print(f"已读取: {item.relative_to(pipeline_dir)}", flush=True)
                except Exception as e:
                    print(f"读取文件 {item.name} 时出错: {e}", flush=True)

    # 收集所有json数据
    collect_json(pipeline_dir)

    # 写入nodes.json
    nodes_file = pipeline_dir / "nodes.json"
    try:
        with open(nodes_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=4)
        print(f"已创建合并文件: {nodes_file}", flush=True)
    except Exception as e:
        print(f"写入nodes.json时出错: {e}", flush=True)
        return

    # 删除原来的文件夹和文件（保留nodes.json）
    for item in pipeline_dir.iterdir():
        if item.name == "nodes.json":
            continue
        try:
            if item.is_dir():
                shutil.rmtree(item)
                print(f"已删除目录: {item.name}", flush=True)
            else:
                item.unlink()
                print(f"已删除文件: {item.name}", flush=True)
        except Exception as e:
            print(f"删除 {item.name} 时出错: {e}", flush=True)


if __name__ == "__main__":
    for pipeline_path in pipeline_paths:
        print(f"\n处理pipeline目录: {pipeline_path}", flush=True)
        print("=" * 50, flush=True)
        merge_json_files(pipeline_path)
        print("=" * 50, flush=True)
