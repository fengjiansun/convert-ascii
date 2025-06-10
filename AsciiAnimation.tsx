import React, { useState, useEffect, useRef, useCallback, CSSProperties } from 'react';
import './AsciiAnimation.css';

// 类型定义
export interface AsciiAnimationProps {
  /** ASCII帧数据数组，每个元素是一帧的字符串 */
  frames?: string[] | null;
  /** 帧数据的URL路径（可选，与frames二选一） */
  framesUrl?: string | null;
  /** 播放帧率，默认30 */
  fps?: number;
  /** 字符颜色，默认'#00FF00' */
  color?: string;
  /** 背景颜色，默认'#000000' */
  backgroundColor?: string;
  /** 字体大小，默认10 */
  fontSize?: number;
  /** 字体族，默认等宽字体 */
  fontFamily?: string;
  /** 透明度，默认1 */
  opacity?: number;
  /** 对比度，默认1 */
  contrast?: number;
  /** 是否自动播放，默认true */
  autoPlay?: boolean;
  /** 是否循环播放，默认true */
  loop?: boolean;
  /** 自定义CSS类名 */
  className?: string;
  /** 内联样式 */
  style?: CSSProperties;
  /** 帧变化回调 */
  onFrameChange?: (frameIndex: number) => void;
  /** 加载完成回调 */
  onLoadComplete?: (frameCount: number) => void;
  /** 加载失败回调 */
  onLoadError?: (error: Error) => void;
  /** 播放状态变化回调 */
  onPlayStateChange?: (isPlaying: boolean) => void;
  /** 组件准备就绪回调 */
  onReady?: () => void;
}

export interface AsciiAnimationRef {
  /** 开始播放动画 */
  play: () => void;
  /** 暂停动画 */
  pause: () => void;
  /** 重置动画到第一帧 */
  reset: () => void;
  /** 跳转到指定帧 */
  goToFrame: (frameIndex: number) => void;
  /** 获取当前帧索引 */
  getCurrentFrame: () => number;
  /** 获取总帧数 */
  getTotalFrames: () => number;
  /** 获取播放状态 */
  getPlayState: () => boolean;
  /** 获取加载状态 */
  getLoadState: () => { isLoading: boolean; loadError: Error | null };
}

// 加载状态枚举
export enum LoadState {
  IDLE = 'idle',
  LOADING = 'loading',
  SUCCESS = 'success',
  ERROR = 'error'
}

const AsciiAnimation = React.forwardRef<AsciiAnimationRef, AsciiAnimationProps>(
  ({
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
    className = '',
    style = {},
    onFrameChange,
    onLoadComplete,
    onLoadError,
    onPlayStateChange,
    onReady,
    ...rest
  }, ref) => {
    // 状态管理
    const [loadedFrames, setLoadedFrames] = useState<string[]>([]);
    const [currentFrame, setCurrentFrame] = useState<number>(0);
    const [isPlaying, setIsPlaying] = useState<boolean>(false);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [loadError, setLoadError] = useState<Error | null>(null);
    
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const asciiRef = useRef<HTMLPreElement>(null);
    
    // 加载帧数据
    const loadFrames = useCallback(async (): Promise<void> => {
      if (frames) {
        setLoadedFrames(frames);
        onLoadComplete?.(frames.length);
        onReady?.();
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
        const loadedFrameData: string[] = [];
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
        onReady?.();
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));
        setLoadError(err);
        onLoadError?.(err);
      } finally {
        setIsLoading(false);
      }
    }, [frames, framesUrl, onLoadComplete, onLoadError, onReady]);
    
    // 播放控制函数
    const startAnimation = useCallback((): void => {
      if (isPlaying || loadedFrames.length === 0) return;
      
      setIsPlaying(true);
      onPlayStateChange?.(true);
      
      const interval = 1000 / fps;
      
      intervalRef.current = setInterval(() => {
        setCurrentFrame(prev => {
          const nextFrame = loop 
            ? (prev + 1) % loadedFrames.length 
            : Math.min(prev + 1, loadedFrames.length - 1);
          
          onFrameChange?.(nextFrame);
          
          // 如果不循环且到达最后一帧，停止播放
          if (!loop && nextFrame === loadedFrames.length - 1) {
            setIsPlaying(false);
            onPlayStateChange?.(false);
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
          }
          
          return nextFrame;
        });
      }, interval);
    }, [isPlaying, loadedFrames.length, fps, loop, onFrameChange, onPlayStateChange]);
    
    const pauseAnimation = useCallback((): void => {
      setIsPlaying(false);
      onPlayStateChange?.(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }, [onPlayStateChange]);
    
    const resetAnimation = useCallback((): void => {
      pauseAnimation();
      setCurrentFrame(0);
      onFrameChange?.(0);
    }, [pauseAnimation, onFrameChange]);
    
    const goToFrame = useCallback((frameIndex: number): void => {
      const validIndex = Math.max(0, Math.min(frameIndex, loadedFrames.length - 1));
      setCurrentFrame(validIndex);
      onFrameChange?.(validIndex);
    }, [loadedFrames.length, onFrameChange]);
    
    // 暴露给父组件的方法
    React.useImperativeHandle(ref, () => ({
      play: startAnimation,
      pause: pauseAnimation,
      reset: resetAnimation,
      goToFrame,
      getCurrentFrame: () => currentFrame,
      getTotalFrames: () => loadedFrames.length,
      getPlayState: () => isPlaying,
      getLoadState: () => ({ isLoading, loadError })
    }), [
      startAnimation, 
      pauseAnimation, 
      resetAnimation, 
      goToFrame, 
      currentFrame, 
      loadedFrames.length, 
      isPlaying, 
      isLoading, 
      loadError
    ]);
    
    // 生命周期
    useEffect(() => {
      loadFrames();
    }, [loadFrames]);
    
    useEffect(() => {
      if (autoPlay && loadedFrames.length > 0 && !isPlaying) {
        startAnimation();
      }
    }, [autoPlay, loadedFrames.length, isPlaying, startAnimation]);
    
    // 当fps变化时重新启动动画
    useEffect(() => {
      if (isPlaying) {
        pauseAnimation();
        startAnimation();
      }
    }, [fps]); // eslint-disable-line react-hooks/exhaustive-deps
    
    // 清理定时器
    useEffect(() => {
      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }, []);
    
    // 渲染内容
    const renderContent = (): JSX.Element => {
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
            fontFamily,
            fontSize: `${fontSize}px`,
            color,
            opacity,
            filter: `contrast(${contrast})`,
          }}
        >
          {loadedFrames[currentFrame]}
        </pre>
      );
    };
    
    return (
      <div 
        className={`ascii-animation ${className}`}
        style={{
          backgroundColor,
          width: '100%',
          height: '100%',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          overflow: 'hidden',
          ...style
        }}
        {...rest}
      >
        {renderContent()}
      </div>
    );
  }
);

AsciiAnimation.displayName = 'AsciiAnimation';

export default AsciiAnimation; 