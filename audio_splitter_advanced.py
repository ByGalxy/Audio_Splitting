import os
import random
import json
from pydub import AudioSegment
from pathlib import Path
from datetime import datetime

class AudioSplitter:
    """高级音频剪切工具类"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']
        
        # 检查FFmpeg依赖
        from pydub.utils import get_encoder_name, get_prober_name, which
        
        # 尝试获取编码器和探测器
        encoder = get_encoder_name()
        prober = get_prober_name()
        
        # 验证是否能找到有效的编码器和探测器
        if encoder == 'ffmpeg' and not which('ffmpeg'):
            raise RuntimeError("FFmpeg未安装或未添加到系统PATH。请从https://ffmpeg.org/安装FFmpeg并确保已添加到PATH环境变量")
        elif encoder == 'avconv' and not which('avconv'):
            raise RuntimeError("Avconv未安装或未添加到系统PATH")
        
        if prober == 'ffprobe' and not which('ffprobe'):
            raise RuntimeError("FFprobe未安装或未添加到系统PATH。FFprobe通常包含在FFmpeg安装包中")
        elif prober == 'avprobe' and not which('avprobe'):
            raise RuntimeError("Avprobe未安装或未添加到系统PATH")
    
    def validate_audio_file(self, file_path):
        """验证音频文件"""
        if not os.path.exists(file_path):
            return False, "文件不存在"
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_formats:
            return False, f"不支持的文件格式。支持的格式: {', '.join(self.supported_formats)}"
        
        return True, "文件有效"
    
    def get_audio_info(self, audio_path):
        """获取音频文件信息"""
        try:
            audio = AudioSegment.from_file(audio_path)
            duration_ms = len(audio)
            duration_min = duration_ms / (60 * 1000)
            
            info = {
                'duration_ms': duration_ms,
                'duration_min': duration_min,
                'channels': audio.channels,
                'frame_rate': audio.frame_rate,
                'sample_width': audio.sample_width,
                'file_size_mb': os.path.getsize(audio_path) / (1024 * 1024)
            }
            return info
        except Exception as e:
            raise Exception(f"无法读取音频文件: {str(e)}")
    
    def calculate_segments(self, total_duration_ms, min_duration_ms, max_duration_ms, strategy='random'):
        """计算剪切方案"""
        segments = []
        current_pos = 0
        
        while current_pos < total_duration_ms:
            remaining_duration = total_duration_ms - current_pos
            
            # 如果剩余时长小于最小时长，合并到上一段
            if remaining_duration < min_duration_ms and segments:
                segments[-1]['end'] = total_duration_ms
                segments[-1]['duration'] = segments[-1]['end'] - segments[-1]['start']
                break
            
            # 根据策略生成段时长
            if strategy == 'random':
                if remaining_duration < max_duration_ms:
                    segment_duration = remaining_duration
                else:
                    segment_duration = random.randint(min_duration_ms, max_duration_ms)
            elif strategy == 'equal':
                # 尽量等分
                remaining_segments = (remaining_duration + max_duration_ms - 1) // max_duration_ms
                segment_duration = remaining_duration // remaining_segments
                segment_duration = max(min_duration_ms, min(segment_duration, max_duration_ms))
            
            segment_end = min(current_pos + segment_duration, total_duration_ms)
            
            segments.append({
                'start': current_pos,
                'end': segment_end,
                'duration': segment_end - current_pos
            })
            
            current_pos = segment_end
        
        return segments
    
    def split_audio(self, audio_path, min_duration, max_duration, strategy='random', 
                   output_format=None, quality='high'):
        """执行音频剪切"""
        
        # 验证文件
        is_valid, message = self.validate_audio_file(audio_path)
        if not is_valid:
            raise Exception(message)
        
        # 获取音频信息
        print("正在分析音频文件...")
        audio_info = self.get_audio_info(audio_path)
        
        print(f"音频信息:")
        print(f"  时长: {audio_info['duration_min']:.2f} 分钟")
        print(f"  声道: {audio_info['channels']}")
        print(f"  采样率: {audio_info['frame_rate']} Hz")
        print(f"  文件大小: {audio_info['file_size_mb']:.1f} MB")
        
        # 转换时长为毫秒
        min_duration_ms = int(min_duration * 60 * 1000)
        max_duration_ms = int(max_duration * 60 * 1000)
        
        # 检查音频长度
        if audio_info['duration_ms'] < min_duration_ms:
            raise Exception("音频文件太短，无法按指定时长剪切")
        
        # 加载音频
        print("正在加载音频文件...")
        audio = AudioSegment.from_file(audio_path)
        segments = self.calculate_segments(
            audio_info['duration_ms'], 
            min_duration_ms, 
            max_duration_ms, 
            strategy
        )
        # 创建输出目录
        input_path = Path(audio_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = input_path.parent / f"{input_path.stem}_split_{timestamp}"
        output_dir.mkdir(exist_ok=True)
        # 确定输出格式
        if output_format is None:
            output_format = input_path.suffix[1:]  # 使用原格式
        print(f"\n将剪切成 {len(segments)} 个片段:")
        print(f"输出目录: {output_dir}")
        # 设置导出参数
        export_params = {}
        if quality == 'high':
            if output_format == 'mp3':
                export_params['bitrate'] = '320k'
            elif output_format == 'wav':
                export_params['parameters'] = ['-acodec', 'pcm_s16le']
        elif quality == 'medium':
            if output_format == 'mp3':
                export_params['bitrate'] = '192k'
        
        # 执行剪切
        results = []
        for i, segment in enumerate(segments, 1):
            start_time = segment['start']
            end_time = segment['end']
            duration_min = segment['duration'] / (60 * 1000)
            
            print(f"处理片段 {i}/{len(segments)}: {duration_min:.2f} 分钟")
            
            # 剪切音频
            audio_segment = audio[start_time:end_time]
            
            # 生成输出文件名
            output_filename = f"{input_path.stem}_part_{i:02d}.{output_format}"
            output_path = output_dir / output_filename
            
            # 导出文件
            audio_segment.export(str(output_path), format=output_format, **export_params)
            
            # 记录结果
            file_size = output_path.stat().st_size / (1024 * 1024)
            results.append({
                'filename': output_filename,
                'duration_min': duration_min,
                'file_size_mb': file_size,
                'start_time': start_time / 1000,
                'end_time': end_time / 1000
            })
        
        # 保存处理报告
        report = {
            'input_file': str(audio_path),
            'processing_time': datetime.now().isoformat(),
            'settings': {
                'min_duration_min': min_duration,
                'max_duration_min': max_duration,
                'strategy': strategy,
                'output_format': output_format,
                'quality': quality
            },
            'input_info': audio_info,
            'output_files': results,
            'summary': {
                'total_segments': len(results),
                'total_output_size_mb': sum(r['file_size_mb'] for r in results)
            }
        }
        report_path = output_dir / 'processing_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 剪切完成！")
        print(f"共生成 {len(results)} 个文件")
        print(f"总大小: {report['summary']['total_output_size_mb']:.1f} MB")
        print(f"处理报告: {report_path}")
        return output_dir, results
def interactive_mode():
    """交互式模式"""
    splitter = AudioSplitter()
    
    print("=== 高级音频剪切工具 ===")
    print(f"支持格式: {', '.join(splitter.supported_formats)}")
    print()
    
    # 获取文件路径
    while True:
        audio_path = input("请输入音频文件路径: ").strip().strip('"')
        is_valid, message = splitter.validate_audio_file(audio_path)
        if is_valid:
            break
        else:
            print(f"❌ {message}")
    
    # 获取时长设置
    while True:
        try:
            min_duration = float(input("最小时长（分钟）: "))
            max_duration = float(input("最大时长（分钟）: "))
            if min_duration > 0 and min_duration > 0:
                break
            else:
                print("请确保最大时长大于最小时长，且都大于0")
        except ValueError:
            print("请输入有效数字")    
    # 选择剪切策略
    print("\n剪切策略:")
    print("1. 随机时长 (random)")
    print("2. 尽量等分 (equal)")
    strategy_choice = input("选择策略 (1-2, 默认1): ").strip() or "1"
    strategy = 'random' if strategy_choice == '1' else 'equal'
    
    # 选择输出格式
    print(f"\n输出格式 (默认保持原格式):")
    print("1. MP3  2. WAV  3. M4A  4. FLAC")
    format_choice = input("选择格式 (1-4, 默认原格式): ").strip()
    format_map = {'1': 'mp3', '2': 'wav', '3': 'm4a', '4': 'flac'}
    output_format = format_map.get(format_choice)
    
    # 选择质量
    print("\n输出质量:")
    print("1. 高质量  2. 中等质量  3. 标准质量")
    quality_choice = input("选择质量 (1-3, 默认1): ").strip() or "1"
    quality_map = {'1': 'high', '2': 'medium', '3': 'standard'}
    quality = quality_map[quality_choice]
    
    try:
        output_dir, results = splitter.split_audio(
            audio_path, min_duration, max_duration, 
            strategy, output_format, quality
        )
        
        print(f"\n生成的文件:")
        for result in results:
            print(f"  - {result['filename']} ({result['duration_min']:.1f}分钟, {result['file_size_mb']:.1f}MB)")
            
    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")

if __name__ == "__main__":
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {str(e)}")
    input("\n按回车键退出...")
