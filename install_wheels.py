#!/usr/bin/env python
# 使用预编译的wheel文件安装依赖
import os
import sys
import subprocess
import platform

def install_with_wheels():
    """
    使用预编译的wheel文件安装需要编译的包
    对于Windows系统，这可以避免安装Visual C++ Build Tools
    """
    print("开始安装预编译的wheel文件...")
    
    # 获取Python版本和系统架构信息
    python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
    system_arch = "win_amd64" if platform.architecture()[0] == "64bit" else "win32"
    
    print(f"Python版本: {python_version}, 系统架构: {system_arch}")
    
    # 要安装的包列表
    packages = [
        "numpy",  # matplotlib和pandas的依赖
        "lxml",
        "pandas",
        "matplotlib"
    ]
    
    # 首先尝试使用pip install --only-binary选项
    print("\n尝试使用pip的--only-binary选项安装预编译版本...")
    for package in packages:
        try:
            cmd = f"pip install {package} --only-binary=:all: --user"
            print(f"执行命令: {cmd}")
            subprocess.check_call(cmd, shell=True)
            print(f"✅ {package} 安装成功!")
        except subprocess.CalledProcessError:
            print(f"❌ {package} 使用--only-binary选项安装失败，尝试其他方法...")
    
    # 如果上面的方法失败，可以引导用户下载预编译的wheel文件
    print("\n如果上述安装失败，您可以从以下网站下载预编译的wheel文件:")
    print("1. Unofficial Windows Binaries for Python Extension Packages:")
    print("   https://www.lfd.uci.edu/~gohlke/pythonlibs/")
    print("2. PyPI上直接下载wheel文件:")
    print("   https://pypi.org/project/pandas/#files")
    print("   https://pypi.org/project/matplotlib/#files")
    print("   https://pypi.org/project/lxml/#files")
    print("\n下载对应Python版本和系统架构的.whl文件后，使用以下命令安装:")
    print("pip install 下载的文件名.whl")
    
    print("\n或者，您可以选择安装Microsoft Visual C++ Build Tools:")
    print("1. 访问: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
    print("2. 下载并安装Build Tools")
    print("3. 确保选择'C++构建工具'工作负载")

if __name__ == "__main__":
    install_with_wheels()
