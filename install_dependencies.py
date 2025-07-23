import subprocess
import sys

def install_dependencies():
    """安装所需的依赖包"""
    
    print("正在安装音频处理依赖...")
    
    try:
        # 安装 pydub
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pydub"])
        print("✅ pydub 安装成功")
        
        print("\n注意: pydub 需要 ffmpeg 来处理各种音频格式")
        print("如果您还没有安装 ffmpeg，请按照以下方式安装:")
        print("\nWindows:")
        print("1. 下载 ffmpeg: https://ffmpeg.org/download.html")
        print("2. 或使用 chocolatey: choco install ffmpeg")
        print("\nmacOS:")
        print("brew install ffmpeg")
        print("\nUbuntu/Debian:")
        print("sudo apt update && sudo apt install ffmpeg")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        print("请手动安装: pip install pydub")

if __name__ == "__main__":
    install_dependencies()
