import React, { useState, useRef } from 'react';
import AsciiAnimation, { AsciiAnimationRef, AsciiAnimationProps } from './AsciiAnimation';

interface ExampleState {
  fps: number;
  color: string;
  backgroundColor: string;
  fontSize: number;
  opacity: number;
  contrast: number;
  autoPlay: boolean;
  loop: boolean;
  currentFrame: number;
  totalFrames: number;
  isPlaying: boolean;
}

const AsciiAnimationExample: React.FC = () => {
  const animationRef = useRef<AsciiAnimationRef>(null);
  const [frames, setFrames] = useState<string[] | null>(null);
  const [loadMethod, setLoadMethod] = useState<'url' | 'array'>('url');
  
  // 控制状态
  const [state, setState] = useState<ExampleState>({
    fps: 30,
    color: '#00FF00',
    backgroundColor: '#000000',
    fontSize: 10,
    opacity: 1,
    contrast: 1,
    autoPlay: true,
    loop: true,
    currentFrame: 0,
    totalFrames: 0,
    isPlaying: false
  });

  // 从URL加载（推荐用于生产环境）
  const handleUrlLoad = () => {
    setFrames(null);
    setLoadMethod('url');
  };

  // 从数组加载（适合少量帧或内嵌数据）
  const handleArrayLoad = async () => {
    try {
      const frameArray: string[] = [];
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

  // 控制方法
  const handlePlay = () => {
    animationRef.current?.play();
  };

  const handlePause = () => {
    animationRef.current?.pause();
  };

  const handleReset = () => {
    animationRef.current?.reset();
  };

  const handleGoToFrame = (frameIndex: number) => {
    animationRef.current?.goToFrame(frameIndex);
  };

  // 更新状态的通用方法
  const updateState = (updates: Partial<ExampleState>) => {
    setState(prev => ({ ...prev, ...updates }));
  };

  // 回调函数
  const handleFrameChange = (frameIndex: number) => {
    updateState({ currentFrame: frameIndex });
  };

  const handleLoadComplete = (frameCount: number) => {
    updateState({ totalFrames: frameCount });
    console.log('加载完成，总帧数:', frameCount);
  };

  const handleLoadError = (error: Error) => {
    console.error('加载失败:', error);
  };

  const handlePlayStateChange = (isPlaying: boolean) => {
    updateState({ isPlaying });
  };

  const handleReady = () => {
    console.log('组件准备就绪');
  };

  const animationProps: AsciiAnimationProps = {
    [loadMethod === 'url' ? 'framesUrl' : 'frames']: loadMethod === 'url' ? './ascii_frames' : frames,
    fps: state.fps,
    color: state.color,
    backgroundColor: state.backgroundColor,
    fontSize: state.fontSize,
    opacity: state.opacity,
    contrast: state.contrast,
    autoPlay: state.autoPlay,
    loop: state.loop,
    onFrameChange: handleFrameChange,
    onLoadComplete: handleLoadComplete,
    onLoadError: handleLoadError,
    onPlayStateChange: handlePlayStateChange,
    onReady: handleReady
  };

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* 控制面板 */}
      <div style={{ 
        padding: '15px', 
        background: '#222', 
        color: '#fff',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '15px',
        alignItems: 'center',
        borderBottom: '1px solid #444'
      }}>
        {/* 加载方式控制 */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <span>加载方式:</span>
          <button 
            onClick={handleUrlLoad}
            style={{
              padding: '5px 12px',
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
              padding: '5px 12px',
              background: loadMethod === 'array' ? '#0F0' : '#555',
              color: loadMethod === 'array' ? '#000' : '#fff',
              border: '1px solid #666',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            数组加载
          </button>
        </div>

        {/* 播放控制 */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button onClick={handlePlay} style={{ padding: '6px 12px', background: '#0F0', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            播放
          </button>
          <button onClick={handlePause} style={{ padding: '6px 12px', background: '#FF6B6B', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            暂停
          </button>
          <button onClick={handleReset} style={{ padding: '6px 12px', background: '#4ECDC4', color: '#000', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            重置
          </button>
        </div>

        {/* 帧控制 */}
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span>帧: {state.currentFrame + 1} / {state.totalFrames}</span>
          <input
            type="range"
            min="0"
            max={Math.max(0, state.totalFrames - 1)}
            value={state.currentFrame}
            onChange={(e) => handleGoToFrame(parseInt(e.target.value))}
            style={{ width: '150px' }}
          />
        </div>

        {/* 状态显示 */}
        <div style={{ 
          padding: '4px 8px', 
          background: state.isPlaying ? '#0F0' : '#666',
          color: state.isPlaying ? '#000' : '#fff',
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          {state.isPlaying ? '播放中' : '已暂停'}
        </div>
      </div>

      {/* 参数控制面板 */}
      <div style={{ 
        padding: '10px 15px', 
        background: '#333', 
        color: '#fff',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '20px',
        borderBottom: '1px solid #444'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ minWidth: '60px' }}>FPS:</label>
          <input
            type="range"
            min="1"
            max="60"
            value={state.fps}
            onChange={(e) => updateState({ fps: parseInt(e.target.value) })}
            style={{ width: '100px' }}
          />
          <span style={{ minWidth: '30px' }}>{state.fps}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ minWidth: '60px' }}>字体大小:</label>
          <input
            type="range"
            min="6"
            max="20"
            value={state.fontSize}
            onChange={(e) => updateState({ fontSize: parseInt(e.target.value) })}
            style={{ width: '100px' }}
          />
          <span style={{ minWidth: '30px' }}>{state.fontSize}px</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label>字符颜色:</label>
          <input
            type="color"
            value={state.color}
            onChange={(e) => updateState({ color: e.target.value })}
            style={{ width: '40px', height: '30px', border: 'none', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label>背景颜色:</label>
          <input
            type="color"
            value={state.backgroundColor}
            onChange={(e) => updateState({ backgroundColor: e.target.value })}
            style={{ width: '40px', height: '30px', border: 'none', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ minWidth: '60px' }}>透明度:</label>
          <input
            type="range"
            min="0.1"
            max="1"
            step="0.1"
            value={state.opacity}
            onChange={(e) => updateState({ opacity: parseFloat(e.target.value) })}
            style={{ width: '100px' }}
          />
          <span style={{ minWidth: '40px' }}>{Math.round(state.opacity * 100)}%</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ minWidth: '60px' }}>对比度:</label>
          <input
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={state.contrast}
            onChange={(e) => updateState({ contrast: parseFloat(e.target.value) })}
            style={{ width: '100px' }}
          />
          <span style={{ minWidth: '40px' }}>{Math.round(state.contrast * 100)}%</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label>
            <input
              type="checkbox"
              checked={state.autoPlay}
              onChange={(e) => updateState({ autoPlay: e.target.checked })}
              style={{ marginRight: '4px' }}
            />
            自动播放
          </label>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label>
            <input
              type="checkbox"
              checked={state.loop}
              onChange={(e) => updateState({ loop: e.target.checked })}
              style={{ marginRight: '4px' }}
            />
            循环播放
          </label>
        </div>
      </div>

      {/* ASCII 动画组件 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <AsciiAnimation 
          ref={animationRef}
          {...animationProps}
        />
      </div>
    </div>
  );
};

export default AsciiAnimationExample; 