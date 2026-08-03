#!/usr/bin/env python3

import platform


def show(title, value):
    """统一打印信息。"""
    print(f"{title}：{value if value else '未知'}")


print("=" * 20, "宿主机基本信息", "=" * 20)

# 获取宿主机综合信息
host = platform.uname()

show("操作系统类型", host.system)
show("主机名", host.node)
show("系统或内核发行版本", host.release)
show("系统或内核详细版本", host.version)
show("CPU机器架构", host.machine)
show("处理器名称", host.processor)

# 返回尽可能完整、适合人阅读的平台描述
show("综合平台信息", platform.platform())

# 返回精简的平台描述
show("精简平台信息", platform.platform(terse=True))

# CPU机器架构，例如 x86_64、AMD64、aarch64、arm64
show("机器架构", platform.machine())

# 处理器名称，某些Linux系统可能返回空字符串
show("处理器", platform.processor())

# 返回当前解释器的位数及二进制格式
# Linux常见：('64bit', 'ELF')
# Windows常见：('64bit', 'WindowsPE')
show("系统位数与二进制格式", platform.architecture())

# 获取系统的常用别名
alias = platform.system_alias(
    platform.system(),
    platform.release(),
    platform.version(),
)

show("系统别名", alias[0])
show("别名发行版本", alias[1])
show("别名详细版本", alias[2])


print("\n" + "=" * 20, "Linux信息", "=" * 20)

if platform.system() == "Linux":
    try:
        # 从 /etc/os-release 或 /usr/lib/os-release 获取发行版信息
        os_release = platform.freedesktop_os_release()

        show("发行版名称", os_release.get("NAME"))
        show("发行版ID", os_release.get("ID"))
        show("发行版版本", os_release.get("VERSION_ID"))
        show("发行版完整名称", os_release.get("PRETTY_NAME"))
        show("发行版详细版本", os_release.get("VERSION"))
        show("发行版代号", os_release.get("VERSION_CODENAME"))
        show("相似发行版", os_release.get("ID_LIKE"))
        show("系统主页", os_release.get("HOME_URL"))
        show("技术支持地址", os_release.get("SUPPORT_URL"))
        show("问题报告地址", os_release.get("BUG_REPORT_URL"))

    except AttributeError:
        print("当前Python版本不支持 freedesktop_os_release()")

    except OSError:
        print("无法读取 /etc/os-release 或 /usr/lib/os-release")

    # 获取C标准库类型和版本，例如 ('glibc', '2.35')
    libc_name, libc_version = platform.libc_ver()

    show("C标准库", libc_name)
    show("C标准库版本", libc_version)

else:
    print("当前不是Linux系统")


print("\n" + "=" * 20, "Windows信息", "=" * 20)

if platform.system() == "Windows":
    windows = platform.win32_ver()

    show("Windows发行版本", windows[0])
    show("Windows版本号", windows[1])
    show("Windows Service Pack", windows[2])
    show("Windows系统类型", windows[3])

    try:
        show("Windows版本类型", platform.win32_edition())
        show("是否为Windows IoT", platform.win32_is_iot())
    except AttributeError:
        print("当前Python版本不支持Windows扩展信息")

else:
    print("当前不是Windows系统")


print("\n" + "=" * 20, "macOS信息", "=" * 20)

if platform.system() == "Darwin":
    macos = platform.mac_ver()

    show("macOS版本", macos[0])
    show("macOS版本信息", macos[1])
    show("macOS机器架构", macos[2])

else:
    print("当前不是macOS系统")


print("\n" + "=" * 20, "架构判断", "=" * 20)

machine = platform.machine().lower()

if machine in ("x86_64", "amd64"):
    print("当前为 x86 64位架构")

elif machine in ("aarch64", "arm64"):
    print("当前为 ARM 64位架构")

elif machine in ("i386", "i686", "x86"):
    print("当前为 x86 32位架构")

elif machine.startswith("arm"):
    print("当前为 ARM 32位架构")

else:
    print("当前架构无法归类：", machine)


print("\n" + "=" * 20, "采集完成", "=" * 20)