import cv2
from PIL import Image, ImageEnhance
import os
import argparse
import json
from typing import Optional, Tuple

# --- 默认配置参数 ---
DEFAULT_CONFIG = {
    # ASCII字符集配置
    "ascii_chars": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "ascii_chars_simple": " .:-=+*#%@",  # 简化字符集
    "ascii_chars_detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    
    # 输出配置
    "output_dir": "ascii_frames",
    "frame_width": 100,  # ASCII画面的宽度（字符数）
    "frame_height": None,  # None表示按比例自动计算
    "aspect_ratio_correction": 0.55,  # 字符宽高比修正系数
    
    # 图像处理配置
    "brightness": 1.0,  # 亮度调整 (0.5-2.0)
    "contrast": 1.0,    # 对比度调整 (0.5-2.0)
    "saturation": 1.0,  # 饱和度调整 (0.0-2.0)
    "sharpness": 1.0,   # 锐度调整 (0.0-2.0)
    "gamma": 1.0,       # 伽马值调整 (0.1-3.0)
    
    # 视频处理配置
    "fps_limit": None,  # 限制输出帧率，None表示使用原始帧率
    "start_time": 0,    # 开始时间（秒）
    "duration": None,   # 处理时长（秒），None表示处理整个视频
    "frame_skip": 1,    # 跳帧间隔，1表示不跳帧
    
    # 输出格式配置
    "invert": False,    # 是否反转明暗
    "add_padding": False,  # 是否添加边框填充
    "padding_char": " ",   # 填充字符
    "mirror_frames": False,  # 是否镜像帧（创建往返动画效果）
}

class AsciiConverter:
    def __init__(self, config: dict = None):
        """初始化ASCII转换器"""
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)
            
        # 设置ASCII字符集
        self.ascii_chars = self.config["ascii_chars"]
        if self.config.get("invert", False):
            self.ascii_chars = self.ascii_chars[::-1]  # 反转字符顺序
    
    def enhance_image(self, img: Image.Image) -> Image.Image:
        """图像增强处理"""
        # 亮度调整
        if self.config["brightness"] != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(self.config["brightness"])
        
        # 对比度调整
        if self.config["contrast"] != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(self.config["contrast"])
        
        # 饱和度调整（仅在转换为灰度前）
        if self.config["saturation"] != 1.0 and img.mode != "L":
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(self.config["saturation"])
        
        # 锐度调整
        if self.config["sharpness"] != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(self.config["sharpness"])
        
        return img
    
    def apply_gamma_correction(self, img: Image.Image) -> Image.Image:
        """应用伽马校正"""
        if self.config["gamma"] == 1.0:
            return img
            
        import numpy as np
        
        # 转换为numpy数组
        img_array = np.array(img)
        
        # 应用伽马校正
        gamma_corrected = np.power(img_array / 255.0, self.config["gamma"]) * 255.0
        gamma_corrected = np.clip(gamma_corrected, 0, 255).astype(np.uint8)
        
        return Image.fromarray(gamma_corrected)
    
    def calculate_dimensions(self, original_width: int, original_height: int) -> Tuple[int, int]:
        """计算目标尺寸"""
        frame_width = self.config["frame_width"]
        frame_height = self.config["frame_height"]
        
        if frame_height is None:
            # 按比例自动计算高度
            aspect_ratio = original_height / float(original_width)
            new_height = int(aspect_ratio * frame_width * self.config["aspect_ratio_correction"])
            return frame_width, new_height
        else:
            return frame_width, frame_height
    
    def image_to_ascii(self, image_path: str) -> str:
        """将单张图片转换为ASCII字符串"""
        try:
            img = Image.open(image_path)
        except Exception as e:
            print(f"无法打开图片: {e}")
            return ""

        # 1. 图像增强
        img = self.enhance_image(img)
        
        # 2. 调整尺寸
        original_width, original_height = img.size
        new_width, new_height = self.calculate_dimensions(original_width, original_height)
        img = img.resize((new_width, new_height))

        # 3. 转换为灰度图
        img = img.convert("L")
        
        # 4. 伽马校正
        img = self.apply_gamma_correction(img)

        # 5. 像素转字符
        pixels = img.getdata()
        ascii_str = ""
        for pixel_value in pixels:
            # 将0-255的灰度值映射到ASCII_CHARS的索引
            index = min(int(pixel_value / 256 * len(self.ascii_chars)), len(self.ascii_chars) - 1)
            ascii_str += self.ascii_chars[index]

        # 6. 拼接成多行字符串
        final_ascii = ""
        for i in range(0, len(ascii_str), new_width):
            line = ascii_str[i:i+new_width]
            if self.config["add_padding"]:
                line = self.config["padding_char"] + line + self.config["padding_char"]
            final_ascii += line + "\n"
        
        # 7. 添加顶部和底部填充
        if self.config["add_padding"]:
            padding_line = self.config["padding_char"] * (new_width + 2) + "\n"
            final_ascii = padding_line + final_ascii + padding_line
            
        return final_ascii

    def video_to_ascii_frames(self, video_path: str, progress_callback: Optional[callable] = None) -> int:
        """将视频或GIF转换为一系列ASCII文本文件"""
        if not os.path.exists(self.config["output_dir"]):
            os.makedirs(self.config["output_dir"])

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"错误：无法打开视频文件 {video_path}")
            return 0

        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 由于FFmpeg可能返回不准确的总帧数，我们需要手动计算
        # 先跳到最后一帧，然后获取当前帧位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame = cap.read()
        if ret:
            actual_total_frames = int(cap.get(cv2.CAP_PROP_POS_FRAMES)) + 1
            print(f"修正前视频信息：{total_frames} 帧，{fps:.2f} FPS")
            print(f"修正后视频信息：{actual_total_frames} 帧，{fps:.2f} FPS")
            total_frames = actual_total_frames
        else:
            print(f"视频信息：{total_frames} 帧，{fps:.2f} FPS")
        
        # 跳回开始位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # 再次验证总帧数 - 通过实际读取所有帧
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
        
        print(f"实际读取帧数：{frame_count} 帧")
        total_frames = frame_count
        
        # 跳回开始位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # 计算处理范围
        start_frame = int(self.config["start_time"] * fps)
        if self.config["duration"]:
            end_frame = min(start_frame + int(self.config["duration"] * fps), total_frames)
        else:
            end_frame = total_frames
        
        # 跳回开始位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # 设置开始位置
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        frame_count = 0
        processed_count = 0
        
        while cap.get(cv2.CAP_PROP_POS_FRAMES) < end_frame:
            success, frame = cap.read()
            if not success:
                break
            
            # 跳帧处理
            if frame_count % self.config["frame_skip"] != 0:
                frame_count += 1
                continue
            
            # FPS限制
            if self.config["fps_limit"] and processed_count > 0:
                target_fps = self.config["fps_limit"]
                if processed_count * target_fps / fps > processed_count:
                    frame_count += 1
                    continue
            
            # 将OpenCV的BGR图像转换为Pillow可以处理的RGB图像
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # 临时保存帧图片，以便image_to_ascii处理
            temp_frame_path = os.path.join(self.config["output_dir"], "_temp_frame.png")
            img.save(temp_frame_path)
            
            # 核心转换
            ascii_art = self.image_to_ascii(temp_frame_path)
            
            # 将ASCII艺术保存为txt文件
            output_file_path = os.path.join(self.config["output_dir"], f"frame_{processed_count:05d}.txt")
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(ascii_art)
            
            print(f"已生成: {output_file_path} ({processed_count + 1}/{end_frame - start_frame})")
            
            # 进度回调
            if progress_callback:
                progress = (processed_count + 1) / (end_frame - start_frame)
                progress_callback(progress, processed_count + 1, end_frame - start_frame)
            
            frame_count += 1
            processed_count += 1
        
        # 清理临时文件
        temp_frame_path = os.path.join(self.config["output_dir"], "_temp_frame.png")
        if os.path.exists(temp_frame_path):
            os.remove(temp_frame_path)
            
        cap.release()
        
        # 如果启用镜像帧，创建往返效果
        if self.config.get("mirror_frames", False) and processed_count > 1:
            print(f"\n正在生成镜像帧...")
            original_count = processed_count
            
            # 从倒数第二帧开始向前复制（避免重复最后一帧）
            for i in range(original_count - 2, -1, -1):
                source_file = os.path.join(self.config["output_dir"], f"frame_{i:05d}.txt")
                target_file = os.path.join(self.config["output_dir"], f"frame_{processed_count:05d}.txt")
                
                if os.path.exists(source_file):
                    with open(source_file, 'r', encoding='utf-8') as src:
                        content = src.read()
                    with open(target_file, 'w', encoding='utf-8') as dst:
                        dst.write(content)
                    processed_count += 1
                    
                    # 进度回调
                    if progress_callback:
                        progress = (processed_count - original_count) / original_count
                        progress_callback(progress, processed_count - original_count, original_count)
            
            print(f"镜像帧生成完成！添加了 {processed_count - original_count} 个镜像帧。")
        
        print(f"\n转换完成！总共 {processed_count} 帧。")
        print(f"文件保存在 '{self.config['output_dir']}' 目录下。")
        
        return processed_count
    
    def save_config(self, config_path: str):
        """保存配置到文件"""
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"配置已保存到: {config_path}")
    
    @classmethod
    def load_config(cls, config_path: str):
        """从文件加载配置"""
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return cls(config)

def main():
    parser = argparse.ArgumentParser(description="视频转ASCII字符动画工具")
    parser.add_argument("input", help="输入视频文件路径")
    parser.add_argument("-o", "--output", default="ascii_frames", help="输出目录 (默认: ascii_frames)")
    parser.add_argument("-w", "--width", type=int, default=100, help="ASCII画面宽度 (默认: 100)")
    parser.add_argument("--height", type=int, help="ASCII画面高度 (默认: 按比例计算)")
    parser.add_argument("--fps", type=float, help="限制输出帧率")
    parser.add_argument("--start", type=float, default=0, help="开始时间(秒) (默认: 0)")
    parser.add_argument("--duration", type=float, help="处理时长(秒)")
    parser.add_argument("--skip", type=int, default=1, help="跳帧间隔 (默认: 1)")
    
    # 图像处理参数
    parser.add_argument("--brightness", type=float, default=1.0, help="亮度调整 (默认: 1.0)")
    parser.add_argument("--contrast", type=float, default=1.0, help="对比度调整 (默认: 1.0)")
    parser.add_argument("--gamma", type=float, default=1.0, help="伽马值调整 (默认: 1.0)")
    
    # 字符集选项
    parser.add_argument("--charset", choices=["simple", "detailed", "custom"], default="detailed", 
                       help="ASCII字符集类型 (默认: detailed)")
    parser.add_argument("--custom-chars", help="自定义ASCII字符集")
    parser.add_argument("--invert", action="store_true", help="反转明暗")
    parser.add_argument("--padding", action="store_true", help="添加边框填充")
    parser.add_argument("--mirror", action="store_true", help="生成镜像帧（往返动画效果）")
    
    # 配置文件
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--save-config", help="保存当前配置到文件")
    
    args = parser.parse_args()
    
    # 构建配置
    config = DEFAULT_CONFIG.copy()
    
    if args.config:
        # 从配置文件加载
        converter = AsciiConverter.load_config(args.config)
    else:
        # 从命令行参数构建配置
        config.update({
            "output_dir": args.output,
            "frame_width": args.width,
            "frame_height": args.height,
            "fps_limit": args.fps,
            "start_time": args.start,
            "duration": args.duration,
            "frame_skip": args.skip,
            "brightness": args.brightness,
            "contrast": args.contrast,
            "gamma": args.gamma,
            "invert": args.invert,
            "add_padding": args.padding,
            "mirror_frames": args.mirror,
        })
        
        # 设置字符集
        if args.charset == "simple":
            config["ascii_chars"] = config["ascii_chars_simple"]
        elif args.charset == "detailed":
            config["ascii_chars"] = config["ascii_chars_detailed"]
        elif args.custom_chars:
            config["ascii_chars"] = args.custom_chars
        
        converter = AsciiConverter(config)
    
    # 保存配置
    if args.save_config:
        converter.save_config(args.save_config)
    
    # 执行转换
    def progress_callback(progress, current, total):
        print(f"\r进度: {progress*100:.1f}% ({current}/{total})", end="", flush=True)
    
    frame_count = converter.video_to_ascii_frames(args.input, progress_callback)
    
    if frame_count > 0:
        print(f"\n✅ 转换成功！共生成 {frame_count} 帧ASCII动画")
        print(f"📁 输出目录: {converter.config['output_dir']}")
        print(f"🎬 建议在网页中使用以下配置：")
        print(f"   framesUrl: './{converter.config['output_dir']}'")
        print(f"   frameCount: {frame_count}")
    else:
        print("❌ 转换失败")

# --- 执行 ---
if __name__ == "__main__":
    # 如果直接运行（不带参数），使用原来的简单模式
    import sys
    if len(sys.argv) == 1:
        print("简单模式运行...")
        converter = AsciiConverter()
        converter.video_to_ascii_frames("./v.mov")
    else:
        main()