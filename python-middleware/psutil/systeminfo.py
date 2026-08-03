#!/usr/bin/env python3
"""使用 psutil 采集当前主机的核心系统指标。"""

import datetime
import os
import socket
import time

try:
    import psutil
except ImportError:
    raise SystemExit("未安装 psutil，请执行：python3 -m pip install psutil")


SAMPLE_SECONDS = 1
TOP_COUNT = 5


def bytes_to_gb(value):
    """把字节转换为 GB，并保留两位小数。"""
    return round(value / 1024**3, 2)


def bytes_to_mb(value):
    """把字节转换为 MB，并保留两位小数。"""
    return round(value / 1024**2, 2)


def print_title(title):
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def collect_processes():
    """采集进程并返回 CPU、内存 Top 列表和异常统计。"""
    processes = []
    errors = {"not_found": 0, "access_denied": 0, "zombie": 0}

    # 第一次调用用于建立 CPU 时间基准，之后等待采样窗口再读取。
    for process in psutil.process_iter():
        try:
            process.cpu_percent(None)
            processes.append(process)
        except psutil.ZombieProcess:
            errors["zombie"] += 1
        except psutil.NoSuchProcess:
            errors["not_found"] += 1
        except psutil.AccessDenied:
            errors["access_denied"] += 1

    return processes, errors


def read_process_results(processes, errors):
    results = []

    for process in processes:
        try:
            # oneshot 会缓存同一次采集所需的底层进程信息，减少 /proc 读取。
            with process.oneshot():
                memory = process.memory_info()
                results.append({
                    "pid": process.pid,
                    "name": process.name(),
                    "username": process.username(),
                    "status": process.status(),
                    "cpu_percent": process.cpu_percent(None),
                    "memory_percent": process.memory_percent(),
                    "memory_rss_mb": bytes_to_mb(memory.rss),
                    "threads": process.num_threads(),
                    "create_time": datetime.datetime.fromtimestamp(
                        process.create_time()
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "cmdline": " ".join(process.cmdline()),
                })
        except psutil.ZombieProcess:
            errors["zombie"] += 1
        except psutil.NoSuchProcess:
            errors["not_found"] += 1
        except psutil.AccessDenied:
            errors["access_denied"] += 1

    top_cpu = sorted(
        results, key=lambda item: item["cpu_percent"], reverse=True
    )[:TOP_COUNT]
    top_memory = sorted(
        results, key=lambda item: item["memory_rss_mb"], reverse=True
    )[:TOP_COUNT]
    return results, top_cpu, top_memory


def print_processes(title, processes):
    print_title(title)
    print("PID      CPU%    MEM%    RSS(MB)   线程   用户         进程")
    for item in processes:
        print(
            f"{item['pid']:<8} "
            f"{item['cpu_percent']:<7.1f} "
            f"{item['memory_percent']:<7.2f} "
            f"{item['memory_rss_mb']:<9.2f} "
            f"{item['threads']:<6} "
            f"{item['username'][:12]:<12} "
            f"{item['name']}"
        )


def main():
    process_samples, process_errors = collect_processes()
    disk_io_before = psutil.disk_io_counters()
    network_before = psutil.net_io_counters()

    # interval 会阻塞指定秒数，用于得到这一时间段内的 CPU 使用率。
    cpu_percent = psutil.cpu_percent(interval=SAMPLE_SECONDS)

    disk_io_after = psutil.disk_io_counters()
    network_after = psutil.net_io_counters()
    all_processes, top_cpu, top_memory = read_process_results(
        process_samples, process_errors
    )

    print_title("系统")
    print("主机名：", socket.gethostname())
    print("系统启动时间：", datetime.datetime.fromtimestamp(
        psutil.boot_time()
    ).strftime("%Y-%m-%d %H:%M:%S"))
    print("系统运行时长：", str(datetime.timedelta(
        seconds=int(time.time() - psutil.boot_time())
    )))
    print("当前登录用户：", len(psutil.users()))
    print("当前进程数量：", len(all_processes))

    print_title("CPU")
    print("逻辑核心数：", psutil.cpu_count(logical=True))
    print("物理核心数：", psutil.cpu_count(logical=False))
    print("CPU 总使用率：", cpu_percent, "%")
    print("每核心使用率：", psutil.cpu_percent(percpu=True))
    print("CPU 累计时间：", psutil.cpu_times())
    try:
        print("系统负载 1/5/15 分钟：", psutil.getloadavg())
    except (AttributeError, OSError):
        print("系统负载：当前平台不支持")
    frequency = psutil.cpu_freq()
    if frequency:
        print("CPU 当前频率：", round(frequency.current, 2), "MHz")

    print_title("内存")
    memory = psutil.virtual_memory()
    print("物理内存总量：", bytes_to_gb(memory.total), "GB")
    print("物理内存已用：", bytes_to_gb(memory.used), "GB")
    print("物理内存可用：", bytes_to_gb(memory.available), "GB")
    print("物理内存使用率：", memory.percent, "%")
    swap = psutil.swap_memory()
    print("Swap 总量：", bytes_to_gb(swap.total), "GB")
    print("Swap 已用：", bytes_to_gb(swap.used), "GB")
    print("Swap 使用率：", swap.percent, "%")

    print_title("磁盘")
    root_disk = psutil.disk_usage("/")
    print("根目录总量：", bytes_to_gb(root_disk.total), "GB")
    print("根目录已用：", bytes_to_gb(root_disk.used), "GB")
    print("根目录剩余：", bytes_to_gb(root_disk.free), "GB")
    print("根目录使用率：", root_disk.percent, "%")
    partitions = psutil.disk_partitions(all=False)
    print("已挂载分区数量：", len(partitions))
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            print(
                f"{partition.device} -> {partition.mountpoint} "
                f"({partition.fstype}) 使用率={usage.percent}% "
                f"剩余={bytes_to_gb(usage.free)}GB"
            )
        except (PermissionError, OSError):
            print(f"{partition.device} -> {partition.mountpoint} 无法读取")

    if disk_io_before and disk_io_after:
        print("采样期磁盘读取速度：", bytes_to_mb(
            (disk_io_after.read_bytes - disk_io_before.read_bytes)
            / SAMPLE_SECONDS
        ), "MB/s")
        print("采样期磁盘写入速度：", bytes_to_mb(
            (disk_io_after.write_bytes - disk_io_before.write_bytes)
            / SAMPLE_SECONDS
        ), "MB/s")
        print("磁盘累计 IO：", disk_io_after)

    print_title("网络")
    print("累计接收：", bytes_to_gb(network_after.bytes_recv), "GB")
    print("累计发送：", bytes_to_gb(network_after.bytes_sent), "GB")
    print("采样期接收速度：", bytes_to_mb(
        (network_after.bytes_recv - network_before.bytes_recv)
        / SAMPLE_SECONDS
    ), "MB/s")
    print("采样期发送速度：", bytes_to_mb(
        (network_after.bytes_sent - network_before.bytes_sent)
        / SAMPLE_SECONDS
    ), "MB/s")
    for name, stats in psutil.net_if_stats().items():
        print(
            f"网卡={name} 启用={stats.isup} "
            f"速率={stats.speed}Mbps MTU={stats.mtu}"
        )

    try:
        connections = psutil.net_connections(kind="tcp")
        established = [
            conn for conn in connections
            if conn.status == psutil.CONN_ESTABLISHED
        ]
        listening = [
            conn for conn in connections
            if conn.status == psutil.CONN_LISTEN
        ]
        print("TCP 连接总数：", len(connections))
        print("ESTABLISHED 数量：", len(established))
        print("LISTEN 数量：", len(listening))
    except psutil.AccessDenied:
        print("TCP 连接：权限不足，请使用 sudo 运行")

    print_title("传感器")
    temperatures = getattr(psutil, "sensors_temperatures", lambda: {})()
    fans = getattr(psutil, "sensors_fans", lambda: {})()
    battery = getattr(psutil, "sensors_battery", lambda: None)()
    print("温度：", temperatures or "未检测到或平台不支持")
    print("风扇：", fans or "未检测到或平台不支持")
    print("电池：", battery or "未检测到或平台不支持")

    print_processes(f"CPU 最高的 {TOP_COUNT} 个进程", top_cpu)
    print_processes(f"内存最高的 {TOP_COUNT} 个进程", top_memory)

    print_title("进程采集异常")
    print("采集期间已退出：", process_errors["not_found"])
    print("权限不足：", process_errors["access_denied"])
    print("僵尸进程：", process_errors["zombie"])

    print_title("当前 Python 进程")
    current = psutil.Process(os.getpid())
    try:
        with current.oneshot():
            print("PID：", current.pid)
            print("名称：", current.name())
            print("状态：", current.status())
            print("父进程 PID：", current.ppid())
            print("线程数：", current.num_threads())
            print("RSS 内存：", bytes_to_mb(current.memory_info().rss), "MB")
            print("启动命令：", " ".join(current.cmdline()))
            print("子进程：", current.children(recursive=True))
    except psutil.ZombieProcess:
        print("当前 Python 进程成为僵尸进程")
    except psutil.NoSuchProcess:
        print("当前 Python 进程已经退出")
    except psutil.AccessDenied:
        print("没有权限读取当前 Python 进程")


if __name__ == "__main__":
    main()
