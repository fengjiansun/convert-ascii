import React, { useState, useEffect, useRef, useCallback } from 'react';
import './AsciiAnimation.css';

/**
 * ASCII动效React组件
 * 
 * @param {Object} props 组件属性
 * @param {string[]} props.frames - ASCII帧数据数组，每个元素是一帧的字符串
 * @param {string} props.framesUrl - 帧数据的URL路径（可选，与frames二选一）
 * @param {number} props.fps - 播放帧率，默认30
 * @param {string} props.color - 字符颜色，默认'#00FF00'
 * @param {string} props.backgroundColor - 背景颜色，默认'#000000'
 * @param {number} props.fontSize - 字体大小，默认10
 * @param {string} props.fontFamily - 字体，默认等宽字体
 * @param {number} props.opacity - 透明度，默认1
 * @param {number} props.contrast - 对比度，默认1
 * @param {boolean} props.autoPlay - 是否自动播放，默认true
 * @param {boolean} props.loop - 是否循环播放，默认true
 * @param {boolean} props.showControls - 是否显示控制面板，默认false
 * @param {Function} props.onFrameChange - 帧变化回调 (frameIndex) => {}
 * @param {Function} props.onLoadComplete - 加载完成回调 (frameCount) => {}
 * @param {Function} props.onLoadError - 加载失败回调 (error) => {}
 */
const AsciiAnimation = ({
  frames = null,
  framesUrl = null,
  fps = 30,
  color = '#00FF00',
  backgroundColor = '#000000',
  fontSize = 10,
  fontFamily = "'Courier New', Courier, monospace",
  opacity = 1,
  contrast = 1,
  autoPlay = true,
  loop = true,
  showControls = false,
  onFrameChange = null,
  onLoadComplete = null,
  onLoadError = null,
  className = '',
  style = {},
  ...rest
}) => {
  // 状态管理
  const [loadedFrames, setLoadedFrames] = useState([]);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);
  
  // 控制面板状态
  const [controlsFps, setControlsFps] = useState(fps);
  const [controlsColor, setControlsColor] = useState(color);
  const [controlsBgColor, setControlsBgColor] = useState(backgroundColor);
  const [controlsFontSize, setControlsFontSize] = useState(fontSize);
  const [controlsFontFamily, setControlsFontFamily] = useState(fontFamily);
  const [controlsOpacity, setControlsOpacity] = useState(opacity);
  const [controlsContrast, setControlsContrast] = useState(contrast);
  
  const intervalRef = useRef(null);
  const asciiRef = useRef(null);
  
  // 加载帧数据
  const loadFrames = useCallback(async () => {
    if (frames) {
      setLoadedFrames(frames);
      onLoadComplete?.(frames.length);
      return;
    }
    
    if (!framesUrl) {
      const error = new Error('必须提供 frames 或 framesUrl');
      setLoadError(error);
      onLoadError?.(error);
      return;
    }
    
    setIsLoading(true);
    setLoadError(null);
    
    try {
      const loadedFrameData = [];
      let frameIndex = 0;
      
      while (true) {
        const frameId = frameIndex.toString().padStart(5, '0');
        const frameUrl = `${framesUrl}/frame_${frameId}.txt`;
        
        try {
          const response = await fetch(frameUrl);
          if (!response.ok) break;
          
          const frameContent = await response.text();
          loadedFrameData.push(frameContent);
          frameIndex++;
        } catch (error) {
          console.warn(`Failed to load frame ${frameIndex}:`, error);
          break;
        }
      }
      
      if (loadedFrameData.length === 0) {
        throw new Error('没有找到有效的帧文件');
      }
      
      setLoadedFrames(loadedFrameData);
      onLoadComplete?.(loadedFrameData.length);
    } catch (error) {
      setLoadError(error);
      onLoadError?.(error);
    } finally {
      setIsLoading(false);
    }
  }, [frames, framesUrl, onLoadComplete, onLoadError]);
  
  // 播放控制
  const startAnimation = useCallback(() => {
    if (isPlaying || loadedFrames.length === 0) return;
    
    setIsPlaying(true);
    const interval = 1000 / controlsFps;
    
    intervalRef.current = setInterval(() => {
      setCurrentFrame(prev => {
        const nextFrame = loop ? (prev + 1) % loadedFrames.length : Math.min(prev + 1, loadedFrames.length - 1);
        onFrameChange?.(nextFrame);
        
        // 如果不循环且到达最后一帧，停止播放
        if (!loop && nextFrame === loadedFrames.length - 1) {
          setIsPlaying(false);
          clearInterval(intervalRef.current);
        }
        
        return nextFrame;
      });
    }, interval);
  }, [isPlaying, loadedFrames.length, controlsFps, loop, onFrameChange]);
  
  const pauseAnimation = useCallback(() => {
    setIsPlaying(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);
  
  const resetAnimation = useCallback(() => {
    pauseAnimation();
    setCurrentFrame(0);
    onFrameChange?.(0);
  }, [pauseAnimation, onFrameChange]);
  
  const goToFrame = useCallback((frameIndex) => {
    const validIndex = Math.max(0, Math.min(frameIndex, loadedFrames.length - 1));
    setCurrentFrame(validIndex);
    onFrameChange?.(validIndex);
  }, [loadedFrames.length, onFrameChange]);
  
  // 生命周期
  useEffect(() => {
    loadFrames();
  }, [loadFrames]);
  
  useEffect(() => {
    if (autoPlay && loadedFrames.length > 0 && !isPlaying) {
      startAnimation();
    }
  }, [autoPlay, loadedFrames.length, isPlaying, startAnimation]);
  
  useEffect(() => {
    if (isPlaying) {
      pauseAnimation();
      startAnimation();
    }
  }, [controlsFps]); // eslint-disable-line react-hooks/exhaustive-deps
  
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
  
  // 渲染内容
  const renderContent = () => {
    if (isLoading) {
      return <div className="ascii-loading">加载中...</div>;
    }
    
    if (loadError) {
      return <div className="ascii-error">加载失败: {loadError.message}</div>;
    }
    
    if (loadedFrames.length === 0) {
      return <div className="ascii-empty">没有可显示的帧</div>;
    }
    
    return (
      <pre
        ref={asciiRef}
        className="ascii-content"
        style={{
          fontFamily: controlsFontFamily,
          fontSize: `${controlsFontSize}px`,
          color: controlsColor,
          opacity: controlsOpacity,
          filter: `contrast(${controlsContrast})`,
        }}
      >
        {loadedFrames[currentFrame]}
      </pre>
    );
  };
  
  const renderControls = () => {
    if (!showControls) return null;
    
    return (
      <div className="ascii-controls">
        <div className="ascii-controls-section">
          <h4>播放控制</h4>
          <div className="ascii-controls-buttons">
            <button 
              onClick={startAnimation} 
              disabled={isPlaying}
              className={`ascii-btn ${isPlaying ? 'active' : ''}`}
            >
              播放
            </button>
            <button 
              onClick={pauseAnimation} 
              disabled={!isPlaying}
              className={`ascii-btn ${!isPlaying ? 'active' : ''}`}
            >
              暂停
            </button>
            <button onClick={resetAnimation} className="ascii-btn">
              重置
            </button>
          </div>
          
          <div className="ascii-control-group">
            <label>帧: {currentFrame + 1} / {loadedFrames.length}</label>
            <input
              type="range"
              min="0"
              max={loadedFrames.length - 1}
              value={currentFrame}
              onChange={(e) => goToFrame(parseInt(e.target.value))}
            />
          </div>
        </div>
        
        <div className="ascii-controls-section">
          <h4>显示设置</h4>
          
          <div className="ascii-control-group">
            <label>播放速度: {controlsFps} FPS</label>
            <input
              type="range"
              min="1"
              max="60"
              value={controlsFps}
              onChange={(e) => setControlsFps(parseInt(e.target.value))}
            />
          </div>
          
          <div className="ascii-control-group">
            <label>字体大小: {controlsFontSize}px</label>
            <input
              type="range"
              min="6"
              max="20"
              value={controlsFontSize}
              onChange={(e) => setControlsFontSize(parseInt(e.target.value))}
            />
          </div>
          
          <div className="ascii-control-group">
            <label>字符颜色</label>
            <input
              type="color"
              value={controlsColor}
              onChange={(e) => setControlsColor(e.target.value)}
            />
          </div>
          
          <div className="ascii-control-group">
            <label>背景颜色</label>
            <input
              type="color"
              value={controlsBgColor}
              onChange={(e) => setControlsBgColor(e.target.value)}
            />
          </div>
          
          <div className="ascii-control-group">
            <label>字体</label>
            <select
              value={controlsFontFamily}
              onChange={(e) => setControlsFontFamily(e.target.value)}
            >
              <option value="'Courier New', Courier, monospace">Courier New</option>
              <option value="'Monaco', 'Menlo', monospace">Monaco</option>
              <option value="'Consolas', monospace">Consolas</option>
              <option value="'Lucida Console', monospace">Lucida Console</option>
            </select>
          </div>
          
          <div className="ascii-control-group">
            <label>透明度: {Math.round(controlsOpacity * 100)}%</label>
            <input
              type="range"
              min="0.1"
              max="1"
              step="0.1"
              value={controlsOpacity}
              onChange={(e) => setControlsOpacity(parseFloat(e.target.value))}
            />
          </div>
          
          <div className="ascii-control-group">
            <label>对比度: {Math.round(controlsContrast * 100)}%</label>
            <input
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              value={controlsContrast}
              onChange={(e) => setControlsContrast(parseFloat(e.target.value))}
            />
          </div>
        </div>
      </div>
    );
  };
  
  return (
    <div 
      className={`ascii-animation ${className}`}
      style={{
        backgroundColor: controlsBgColor,
        ...style
      }}
      {...rest}
    >
      <div className="ascii-display">
        {renderContent()}
      </div>
      {renderControls()}
    </div>
  );
};

export default AsciiAnimation; 