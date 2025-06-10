# 🎬 ASCII 字符动效转换器

一个强大的视频转ASCII字符动画工具，支持将任意视频文件转换为字符动效，并提供网页预览和React/TypeScript组件化方案。

## ✨ 功能特性

### 🎯 核心功能
- **视频转换**：支持 MP4、MOV、AVI、GIF 等多种视频格式
- **实时预览**：内置网页播放器，支持实时参数调整
- **React组件**：完整的TypeScript支持，类型安全的React组件
- **高度可定制**：丰富的参数配置，满足各种使用场景

### 🎨 视觉效果
- **多种字符集**：简化、详细、自定义字符集选择
- **图像增强**：亮度、对比度、饱和度、锐度、伽马值调整
- **样式定制**：颜色、字体、透明度、对比度实时调整
- **播放控制**：通过ref API实现完整的播放控制

### 🚀 高级特性
- **智能处理**：自动帧率检测、跳帧优化、内存管理
- **批量处理**：支持视频片段截取、帧间隔控制
- **配置管理**：JSON配置文件支持，便于批量处理
- **类型安全**：完整的TypeScript类型定义

## 📦 安装

### 环境要求
- Python 3.7+
- Node.js 14+ (如果使用React组件)
- TypeScript 4.0+ (如果使用TypeScript)

### 安装依赖
```bash
# 克隆项目
git clone <项目地址>
cd convert-ascii

# 安装Python依赖
pip install -r requirements.txt

# 如果使用React/TypeScript组件
npm install react react-dom @types/react @types/react-dom typescript
```

## 🎮 快速开始

### 1. 基础转换
```bash
# 最简单的使用方式
python convert.py your_video.mp4
```

这将在 `ascii_frames` 目录下生成ASCII字符文件。

### 2. 网页预览
```bash
# 启动本地服务器预览
python -m http.server 8000
```

然后在浏览器中打开 `http://localhost:8000/index.html`

### 3. React/TypeScript组件使用

#### 基础使用
```tsx
import React from 'react';
import AsciiAnimation from './AsciiAnimation';

function App() {
  return (
    <AsciiAnimation 
      framesUrl="./ascii_frames"
      fps={30}
      autoPlay={true}
    />
  );
}
```

#### 完整控制示例
```tsx
import React, { useRef, useState } from 'react';
import AsciiAnimation, { AsciiAnimationRef } from './AsciiAnimation';

function AdvancedExample() {
  const animationRef = useRef<AsciiAnimationRef>(null);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const handlePlay = () => {
    animationRef.current?.play();
  };

  const handlePause = () => {
    animationRef.current?.pause();
  };

  const handleGoToFrame = (frame: number) => {
    animationRef.current?.goToFrame(frame);
  };

  return (
    <div>
      {/* 自定义控制面板 */}
      <div>
        <button onClick={handlePlay}>播放</button>
        <button onClick={handlePause}>暂停</button>
        <span>当前帧: {currentFrame}</span>
        <span>状态: {isPlaying ? '播放中' : '已暂停'}</span>
      </div>

      {/* ASCII动画组件 */}
      <AsciiAnimation 
        ref={animationRef}
        framesUrl="./ascii_frames"
        fps={24}
        color="#00FF00"
        backgroundColor="#000000"
        fontSize={12}
        opacity={0.9}
        contrast={1.2}
        autoPlay={false}
        loop={true}
        onFrameChange={setCurrentFrame}
        onPlayStateChange={setIsPlaying}
        onLoadComplete={(count) => console.log(`加载了 ${count} 帧`)}
        onLoadError={(error) => console.error('加载失败:', error)}
        onReady={() => console.log('组件准备完毕')}
      />
    </div>
  );
}
```

## 🔧 详细使用说明

### 命令行工具

#### 基础命令
```bash
# 指定输出目录和尺寸
python convert.py video.mp4 -o output_frames -w 150

# 处理视频片段（从第10秒开始，处理30秒）
python convert.py video.mp4 --start 10 --duration 30

# 跳帧处理（每2帧取1帧）
python convert.py video.mp4 --skip 2 --fps 15
```

#### 图像增强
```bash
# 调整视觉效果
python convert.py video.mp4 \
  --brightness 1.2 \
  --contrast 1.1 \
  --gamma 0.9 \
  --charset simple
```

#### 高级选项
```bash
# 使用配置文件
python convert.py video.mp4 --config custom_config.json

# 保存当前配置
python convert.py video.mp4 --save-config my_settings.json

# 反转明暗并添加边框
python convert.py video.mp4 --invert --padding
```

### 配置文件

创建 `config.json` 文件自定义所有参数：

```json
{
  "frame_width": 120,
  "brightness": 1.2,
  "contrast": 1.1,
  "gamma": 0.9,
  "fps_limit": 24,
  "ascii_chars": " .:-=+*#%@",
  "invert": false,
  "add_padding": true
}
```

## 📚 React/TypeScript 组件 API

### AsciiAnimation 组件属性

```tsx
interface AsciiAnimationProps {
  // 数据源（二选一）
  frames?: string[] | null;              // 预加载的帧数组
  framesUrl?: string | null;             // 帧文件目录路径
  
  // 播放设置
  fps?: number;                          // 播放帧率，默认30
  autoPlay?: boolean;                    // 自动播放，默认true
  loop?: boolean;                        // 循环播放，默认true
  
  // 视觉样式
  color?: string;                        // 字符颜色，默认'#00FF00'
  backgroundColor?: string;              // 背景颜色，默认'#000000'
  fontSize?: number;                     // 字体大小，默认10
  fontFamily?: string;                   // 字体族，默认等宽字体
  opacity?: number;                      // 透明度，默认1
  contrast?: number;                     // 对比度，默认1
  
  // 样式控制
  className?: string;                    // 自定义CSS类名
  style?: React.CSSProperties;          // 内联样式
  
  // 事件回调
  onFrameChange?: (frameIndex: number) => void;          // 帧变化回调
  onLoadComplete?: (frameCount: number) => void;         // 加载完成回调
  onLoadError?: (error: Error) => void;                  // 加载失败回调
  onPlayStateChange?: (isPlaying: boolean) => void;      // 播放状态变化回调
  onReady?: () => void;                                  // 组件准备就绪回调
}
```

### Ref API 方法

```tsx
interface AsciiAnimationRef {
  play: () => void;                                      // 开始播放动画
  pause: () => void;                                     // 暂停动画
  reset: () => void;                                     // 重置动画到第一帧
  goToFrame: (frameIndex: number) => void;               // 跳转到指定帧
  getCurrentFrame: () => number;                         // 获取当前帧索引
  getTotalFrames: () => number;                          // 获取总帧数
  getPlayState: () => boolean;                           // 获取播放状态
  getLoadState: () => {                                  // 获取加载状态
    isLoading: boolean; 
    loadError: Error | null;
  };
}
```

### 使用 Ref 进行精确控制

```tsx
import React, { useRef, useEffect } from 'react';
import AsciiAnimation, { AsciiAnimationRef } from './AsciiAnimation';

function ControlledPlayer() {
  const playerRef = useRef<AsciiAnimationRef>(null);

  useEffect(() => {
    const player = playerRef.current;
    if (!player) return;

    // 等待加载完成后执行自定义逻辑
    const checkReady = () => {
      const { isLoading } = player.getLoadState();
      if (!isLoading) {
        // 跳转到第10帧开始播放
        player.goToFrame(10);
        player.play();
      } else {
        setTimeout(checkReady, 100);
      }
    };

    checkReady();
  }, []);

  const handleCustomControl = () => {
    const player = playerRef.current;
    if (!player) return;

    const currentFrame = player.getCurrentFrame();
    const totalFrames = player.getTotalFrames();
    
    if (currentFrame < totalFrames / 2) {
      // 如果在前半段，跳到后半段
      player.goToFrame(Math.floor(totalFrames / 2));
    } else {
      // 否则重置到开头
      player.reset();
    }
  };

  return (
    <div>
      <button onClick={handleCustomControl}>
        智能跳转
      </button>
      
      <AsciiAnimation 
        ref={playerRef}
        framesUrl="./ascii_frames"
        autoPlay={false}
        onReady={() => console.log('播放器就绪')}
      />
    </div>
  );
}
```

## 📁 项目结构

```
convert-ascii/
├── convert.py                 # 核心转换工具
├── index.html                 # 网页预览器
├── requirements.txt           # Python依赖
├── example_config.json        # 配置示例
├── README.md                  # 说明文档
│
├── AsciiAnimation.tsx         # TypeScript React组件
├── AsciiAnimation.css         # 组件样式
├── AsciiAnimationExample.tsx  # 使用示例
│
├── ascii_frames/              # 输出目录
│   ├── frame_00000.txt
│   ├── frame_00001.txt
│   └── ...
│
└── v.mov                      # 示例视频文件
```

## ⚙️ 参数详解

### 核心参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `frame_width` | int | 100 | ASCII画面宽度（字符数） |
| `frame_height` | int? | None | ASCII画面高度（None=自动计算） |
| `aspect_ratio_correction` | float | 0.55 | 字符宽高比修正系数 |

### 图像处理参数

| 参数 | 类型 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| `brightness` | float | 0.5-2.0 | 1.0 | 亮度调整 |
| `contrast` | float | 0.5-2.0 | 1.0 | 对比度调整 |
| `saturation` | float | 0.0-2.0 | 1.0 | 饱和度调整 |
| `sharpness` | float | 0.0-2.0 | 1.0 | 锐度调整 |
| `gamma` | float | 0.1-3.0 | 1.0 | 伽马值调整 |

### 视频处理参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `fps_limit` | float? | 限制输出帧率 |
| `start_time` | float | 开始时间（秒） |
| `duration` | float? | 处理时长（秒） |
| `frame_skip` | int | 跳帧间隔 |

### 字符集选项

| 选项 | 字符集 | 适用场景 |
|------|--------|----------|
| `simple` | ` .:-=+*#%@` | 简单场景，文件较小 |
| `detailed` | ` .'`^",:;Il!i><~+...` | 详细场景，效果更好 |
| `custom` | 自定义 | 特殊需求 |

## 🎨 使用技巧

### 1. 优化转换质量
```bash
# 提高细节表现
python convert.py video.mp4 -w 150 --charset detailed --sharpness 1.2

# 增强对比度
python convert.py video.mp4 --contrast 1.3 --gamma 0.8
```

### 2. 控制文件大小
```bash
# 减少帧数
python convert.py video.mp4 --fps 15 --skip 2

# 使用简单字符集
python convert.py video.mp4 --charset simple -w 80
```

### 3. 处理特定场景
```bash
# 处理黑暗场景
python convert.py dark_video.mp4 --brightness 1.5 --gamma 0.7

# 处理高对比度场景
python convert.py high_contrast.mp4 --invert --contrast 0.8
```

## 🌐 网页集成

### 基础集成
```html
<!-- 引入样式 -->
<link rel="stylesheet" href="AsciiAnimation.css">

<!-- 容器 -->
<div id="ascii-container"></div>

<!-- 脚本 -->
<script src="your-ascii-player.js"></script>
```

### 响应式适配
```css
.ascii-animation {
  width: 100%;
  height: 100vh;
}

@media (max-width: 768px) {
  .ascii-animation {
    font-size: 8px;
  }
}
```

## 🔧 TypeScript 配置

### tsconfig.json 示例
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["DOM", "DOM.Iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": [
    "src"
  ]
}
```

### 类型定义文件
如果需要在纯JavaScript项目中使用，可以创建 `AsciiAnimation.d.ts`：

```typescript
declare module './AsciiAnimation' {
  import { Component } from 'react';
  
  export interface AsciiAnimationProps {
    frames?: string[] | null;
    framesUrl?: string | null;
    fps?: number;
    color?: string;
    backgroundColor?: string;
    fontSize?: number;
    fontFamily?: string;
    opacity?: number;
    contrast?: number;
    autoPlay?: boolean;
    loop?: boolean;
    className?: string;
    style?: React.CSSProperties;
    onFrameChange?: (frameIndex: number) => void;
    onLoadComplete?: (frameCount: number) => void;
    onLoadError?: (error: Error) => void;
    onPlayStateChange?: (isPlaying: boolean) => void;
    onReady?: () => void;
  }
  
  export interface AsciiAnimationRef {
    play: () => void;
    pause: () => void;
    reset: () => void;
    goToFrame: (frameIndex: number) => void;
    getCurrentFrame: () => number;
    getTotalFrames: () => number;
    getPlayState: () => boolean;
    getLoadState: () => { isLoading: boolean; loadError: Error | null };
  }
  
  const AsciiAnimation: React.ForwardRefExoticComponent<
    AsciiAnimationProps & React.RefAttributes<AsciiAnimationRef>
  >;
  
  export default AsciiAnimation;
}
```

## 🚀 性能优化

### 1. 转换优化
- 使用适当的 `frame_width`（建议80-150）
- 合理设置 `frame_skip` 减少帧数
- 使用 `fps_limit` 控制输出帧率

### 2. 加载优化
- 使用 `framesUrl` 方式按需加载
- 对大量帧文件启用gzip压缩
- 考虑使用CDN托管帧文件

### 3. 播放优化
- 合理设置播放帧率（推荐15-30fps）
- 使用CSS硬件加速
- 避免在低性能设备上使用过高分辨率

### 4. React性能优化
```tsx
// 使用 React.memo 避免不必要的重渲染
const OptimizedAsciiAnimation = React.memo(AsciiAnimation);

// 使用 useMemo 缓存计算结果
const memoizedProps = useMemo(() => ({
  framesUrl: './ascii_frames',
  fps: 30,
  color: '#00FF00'
}), []);

// 使用 useCallback 缓存回调函数
const handleFrameChange = useCallback((frame: number) => {
  console.log('Current frame:', frame);
}, []);
```

## 🔍 故障排除

### 常见问题

**1. TypeScript 类型错误**
```bash
# 确保安装了类型定义
npm install @types/react @types/react-dom
```

**2. 模块导入错误**
```bash
# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

**3. 内存不足**
```bash
# 减少处理尺寸
python convert.py video.mp4 -w 80 --skip 2
```

**4. 帧文件加载失败**
- 检查文件路径是否正确
- 确保启用了本地服务器
- 检查CORS设置

**5. React Ref 类型问题**
```tsx
// 正确的 ref 类型定义
const animationRef = useRef<AsciiAnimationRef>(null);

// 使用时进行空值检查
const handleClick = () => {
  animationRef.current?.play();
};
```

## 📄 许可证

本项目采用 MIT 许可证。详见 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境搭建
```bash
# 克隆仓库
git clone <项目地址>
cd convert-ascii

# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖
npm install

# TypeScript编译
npx tsc --noEmit

# 运行测试
python -m pytest tests/
npm test
```

### 代码规范
- Python代码遵循 PEP 8 规范
- TypeScript代码使用 ESLint + Prettier
- 提交信息遵循 Conventional Commits 规范

## 📞 支持

如果你在使用过程中遇到问题，可以：

1. 查看 [常见问题](#-故障排除)
2. 提交 [Issue](项目地址/issues)
3. 参考 [示例代码](./AsciiAnimationExample.tsx)
4. 查看 [类型定义](./AsciiAnimation.tsx)

---

**⭐ 如果这个项目对你有帮助，请给个星标支持一下！** 