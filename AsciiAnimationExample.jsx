import React, { useState, useEffect } from 'react';
import AsciiAnimation from './AsciiAnimation';

const AsciiAnimationExample = () => {
  const [frames, setFrames] = useState(null);
  const [loadMethod, setLoadMethod] = useState('url'); // 'url' 或 'array'

  // 示例：从URL加载（推荐用于生产环境）
  const handleUrlLoad = () => {
    setFrames(null);
    setLoadMethod('url');
  };

  // 示例：从数组加载（适合少量帧或内嵌数据）
  const handleArrayLoad = async () => {
    try {
      // 这里演示如何预加载所有帧到数组中
      const frameArray = [];
      for (let i = 0; i < 10; i++) { // 只加载前10帧作为示例
        const frameId = i.toString().padStart(5, '0');
        const response = await fetch(`./ascii_frames/frame_${frameId}.txt`);
        if (response.ok) {
          const frameContent = await response.text();
          frameArray.push(frameContent);
        }
      }
      setFrames(frameArray);
      setLoadMethod('array');
    } catch (error) {
      console.error('Failed to preload frames:', error);
    }
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 控制面板 */}
      <div style={{ 
        padding: '10px', 
        background: '#222', 
        color: '#fff',
        display: 'flex',
        gap: '10px',
        alignItems: 'center'
      }}>
        <span>加载方式:</span>
        <button 
          onClick={handleUrlLoad}
          style={{
            padding: '5px 10px',
            background: loadMethod === 'url' ? '#0F0' : '#555',
            color: loadMethod === 'url' ? '#000' : '#fff',
            border: '1px solid #666',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          URL 加载
        </button>
        <button 
          onClick={handleArrayLoad}
          style={{
            padding: '5px 10px',
            background: loadMethod === 'array' ? '#0F0' : '#555',
            color: loadMethod === 'array' ? '#000' : '#fff',
            border: '1px solid #666',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          数组加载 (前10帧)
        </button>
      </div>

      {/* ASCII 动画组件 */}
      <div style={{ flex: 1 }}>
        {loadMethod === 'url' ? (
          <AsciiAnimation 
            framesUrl="./ascii_frames"
            fps={30}
            color="#00FF00"
            backgroundColor="#000000"
            fontSize={10}
            autoPlay={true}
            loop={true}
            showControls={true}
            onFrameChange={(frameIndex) => {
              console.log('当前帧:', frameIndex);
            }}
            onLoadComplete={(frameCount) => {
              console.log('加载完成，总帧数:', frameCount);
            }}
            onLoadError={(error) => {
              console.error('加载失败:', error);
            }}
          />
        ) : (
          <AsciiAnimation 
            frames={frames}
            fps={15}
            color="#FF6B6B"
            backgroundColor="#1A1A1A"
            fontSize={12}
            autoPlay={true}
            loop={true}
            showControls={true}
            onFrameChange={(frameIndex) => {
              console.log('当前帧:', frameIndex);
            }}
            onLoadComplete={(frameCount) => {
              console.log('加载完成，总帧数:', frameCount);
            }}
          />
        )}
      </div>
    </div>
  );
};

export default AsciiAnimationExample;

/* 
// 其他使用示例：

// 1. 最简单的使用方式
<AsciiAnimation framesUrl="./ascii_frames" />

// 2. 自定义样式
<AsciiAnimation 
  framesUrl="./ascii_frames"
  color="#FF0000"
  backgroundColor="#000000"
  fontSize={12}
  fps={24}
  showControls={false}
/>

// 3. 使用预加载的帧数组
const myFrames = ['frame1', 'frame2', 'frame3'];
<AsciiAnimation 
  frames={myFrames}
  autoPlay={false}
  showControls={true}
/>

// 4. 带回调的完整配置
<AsciiAnimation 
  framesUrl="./ascii_frames"
  fps={30}
  color="#00FF00"
  backgroundColor="#000000"
  fontSize={10}
  fontFamily="'Monaco', monospace"
  opacity={0.9}
  contrast={1.2}
  autoPlay={true}
  loop={true}
  showControls={true}
  className="my-custom-class"
  style={{ border: '2px solid #0F0' }}
  onFrameChange={(frameIndex) => console.log('Frame:', frameIndex)}
  onLoadComplete={(count) => console.log('Loaded:', count)}
  onLoadError={(error) => console.error('Error:', error)}
/>
*/ 