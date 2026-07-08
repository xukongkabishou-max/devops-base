#!/usr/bin/env python3
import os
import platform
import psutil
import subprocess
import json

try:
    import GPUtil
except ImportError:
    GPUtil = None


# =======================
# 基础信息
# =======================

def get_os_info():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return platform.platform()


def get_architecture():
    arch = platform.machine().lower()
    if "arm" in arch:
        return "arm"
    if "x86" in arch or "amd" in arch or "intel" in arch:
        return "x86"
    return arch


def get_cpu_cores():
    return os.cpu_count()


def get_memory():
    return round(psutil.virtual_memory().total / (1024 ** 3), 1)


# =======================
# GPU
# =======================

def get_gpu_info():
    if GPUtil is None:
        return "未安装 GPUtil"

    gpus = GPUtil.getGPUs()
    if not gpus:
        return "未检测到 GPU"

    total = 0
    lines = []
    for i, g in enumerate(gpus):
        mem = round(g.memoryTotal / 1024, 1)
        total += g.memoryTotal
        lines.append(f"  - GPU {i}: {g.name}, 显存: {mem} GB")

    return (
        f"GPU 数量: {len(gpus)}\n"
        f"总显存: {round(total / 1024, 1)} GB\n"
        + "\n".join(lines)
    )


# =======================
# 存储（显示磁盘 → 分区 → 挂载点）
# =======================

def get_disk_info():
    """
    每块物理磁盘清晰展示：
    - 磁盘大小
    - 分区数量
    - 每个分区的大小 / 挂载点 / 是否 LVM
    """
    result = subprocess.run(
        ["lsblk", "-J", "-o", "NAME,TYPE,SIZE,MOUNTPOINT,FSTYPE"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    lines = []

    for dev in data["blockdevices"]:
        if dev["type"] != "disk":
            continue
        if dev["name"].startswith("loop"):
            continue

        disk = dev["name"]
        size = dev["size"]
        children = dev.get("children", []) or []

        lines.append(f"磁盘 {disk} ({size})")
        lines.append(f"  分区数量: {len(children)}")

        if not children:
            lines.append("  - 无分区")
            continue

        for part in children:
            pname = part["name"]
            psize = part["size"]
            mount = part["mountpoint"] or "-"
            fstype = part["fstype"] or "-"
            lines.append(
                f"  - {pname:<10} {psize:<8} 挂载点: {mount:<12} 类型: {fstype}"
            )

        lines.append("")

    return "\n".join(lines).rstrip()


# =======================
# 主入口
# =======================

if __name__ == "__main__":
    print("=== 系统基础信息 ===")
    print(f"操作系统: {get_os_info()}")
    print(f"CPU 核心数: {get_cpu_cores()}")
    print(f"内存大小: {get_memory()} GB")
    print(f"机器架构: {get_architecture()}")

    print("\n=== 存储信息 ===")
    print(get_disk_info())

    print("\n=== GPU 信息 ===")
    print(get_gpu_info())
