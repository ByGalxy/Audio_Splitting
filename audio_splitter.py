import os
import random
from pydub import AudioSegment
from pathlib import Path

def split_audio_file():
    """
    音频文件剪切工具
    将一个大音频文件剪切成多个随机时长的小文件
    """
    
    print("=== 音频文件剪切工具 ===")
    print()
    
    # 获取用户输入
    while True:
        audio_path = input("请输入音频文件的完整路径: ").strip().strip('"')
        if os.path.exists(audio_path):
            break
        else:
            print("文件不存在，请重新输入！")
    
    # 获取时长设置
    while True:
        try:
            min_duration = float(input("请输入最小时长（分钟）: "))
            max_duration = float(input("请输入最大时长（分钟）: "))
            if min_duration > 0 and max_duration > min_duration:
                break
            else:
                print("请确保最大时长大于最小时长，且都大于0！")
        except ValueError:
            print("请输入有效的数字！")
    
    # 转换为毫秒
    min_duration_ms = int(min_duration * 60 * 1000)
    max_duration_ms = int(max_duration * 60 * 1000)
    
    try:
        # 加载音频文件
        print(f"\n正在加载音频文件: {audio_path}")
        audio = AudioSegment.from_file(audio_path)
        total_duration_ms = len(audio)
        total_duration_min = total_duration_ms / (60 * 1000)
        
        print(f"音频总时长: {total_duration_min:.2f} 分钟")
        
        # 检查音频是否足够长
        if total_duration_ms < min_duration_ms:
            print("音频文件太短，无法按指定时长剪切！")
            return
        
        # 创建输出文件夹
        input_path = Path(audio_path)
        output_dir = input_path.parent / f"{input_path.stem}_split"
        output_dir.mkdir(exist_ok=True)
        
        print(f"输出文件夹: {output_dir}")
        
        # 计算剪切方案
        segments = []
        current_pos = 0
        segment_count = 0
        
        while current_pos < total_duration_ms:
            # 计算剩余时长
            remaining_duration = total_duration_ms - current_pos
            
            # 如果剩余时长小于最小时长，合并到上一段
            if remaining_duration < min_duration_ms and segments:
                segments[-1]['end'] = total_duration_ms
                break
            
            # 随机生成当前段的时长
            if remaining_duration < max_duration_ms:
                segment_duration = remaining_duration
            else:
                segment_duration = random.randint(min_duration_ms, max_duration_ms)
            
            segment_end = min(current_pos + segment_duration, total_duration_ms)
            
            segments.append({
                'start': current_pos,
                'end': segment_end,
                'duration': segment_end - current_pos
            })
            
            current_pos = segment_end
            segment_count += 1
        
        print(f"\n将剪切成 {len(segments)} 个片段:")
        
        # 执行剪切
        for i, segment in enumerate(segments, 1):
            start_time = segment['start']
            end_time = segment['end']
            duration_min = segment['duration'] / (60 * 1000)
            
            print(f"片段 {i}: {duration_min:.2f} 分钟 ({start_time/1000:.1f}s - {end_time/1000:.1f}s)")
            
            # 剪切音频
            audio_segment = audio[start_time:end_time]
            
            # 生成输出文件名
            output_filename = f"{input_path.stem}_part_{i:02d}{input_path.suffix}"
            output_path = output_dir / output_filename
            
            # 导出文件
            audio_segment.export(str(output_path), format=input_path.suffix[1:])
            
        print(f"\n✅ 剪切完成！共生成 {len(segments)} 个文件")
        print(f"文件保存在: {output_dir}")
        
        # 显示文件列表
        print("\n生成的文件:")
        for file in sorted(output_dir.glob(f"{input_path.stem}_part_*{input_path.suffix}")):
            file_size = file.stat().st_size / (1024 * 1024)  # MB
            print(f"  - {file.name} ({file_size:.1f} MB)")
            
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {str(e)}")
        print("请检查文件格式是否支持，常见支持格式: mp3, wav, m4a, flac")

def main():
    """主函数"""
    try:
        split_audio_file()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序运行出错: {str(e)}")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
