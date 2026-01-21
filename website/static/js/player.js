/**
 * Banana Player - .ban 格式视频播放器
 * 前端播放逻辑
 */

class BananaPlayer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.canvas = null;
        this.ctx = null;
        this.isPlaying = false;
        this.currentFrame = 0;
        this.totalFrames = 0;
        this.fps = 30;
        this.animationId = null;
        this.lastFrameTime = 0;
        this.frameInterval = 1000 / 30;
        this.isBanFormat = false;
        this.frames = [];
        this.standardVideo = null;
        this.volume = 1;
        this.isMuted = false;
        
        this.init();
    }
    
    init() {
        // 清空容器
        this.container.innerHTML = '';
        
        // 初始化标准视频元素
        this.standardVideo = document.getElementById('standard-video');
        if (this.standardVideo) {
            this.setupStandardVideoEvents();
        }
    }
    
    setupStandardVideoEvents() {
        if (!this.standardVideo) return;
        
        this.standardVideo.addEventListener('loadedmetadata', () => {
            this.canvas.width = this.standardVideo.videoWidth;
            this.canvas.height = this.standardVideo.videoHeight;
        });
        
        this.standardVideo.addEventListener('play', () => {
            this.isPlaying = true;
            this.updatePlayButton();
            this.renderFrame();
        });
        
        this.standardVideo.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayButton();
            cancelAnimationFrame(this.animationId);
        });
        
        this.standardVideo.addEventListener('ended', () => {
            this.isPlaying = false;
            this.updatePlayButton();
        });
        
        this.standardVideo.addEventListener('timeupdate', () => {
            this.updateProgress();
        });
    }
    
    async loadBanVideo(filename) {
        this.isBanFormat = true;
        this.filename = filename;
        this.watchLimitReached = false;
        
        try {
            this.showLoading();
            
            // 获取视频信息
            const infoResponse = await fetch(`/api/video/${filename}/info`);
            const infoData = await infoResponse.json();
            
            if (infoData.error) {
                throw new Error(infoData.error);
            }
            
            // 检查CDN配置
            if (window.CDN_ENABLED) {
                this.useCDN = true;
                this.cdnBaseUrl = window.CDN_BASE_URL;
            }
            
            this.fps = infoData.info.fps || 30;
            this.totalFrames = infoData.info.frame_count || 0;
            this.frameInterval = 1000 / this.fps;
            
            // 计算15秒限制对应的帧数
            this.maxWatchFrames = Math.floor(15 * this.fps);
            
            // 解码视频
            await this.decodeBanVideo(filename);
            
            this.hideLoading();
            this.renderFrame();
            this.updateTimeDisplay();
            
            // 显示15秒限制提示
            this.showWatchLimitWarning();
            
        } catch (error) {
            console.error('加载视频失败:', error);
            this.showError(error.message);
        }
    }
    
    async decodeBanVideo(filename) {
        this.frames = [];
        
        // 批量加载帧数据（每次加载50帧，但限制在15秒内）
        const batchSize = 50;
        let loadedFrames = 0;
        const maxFramesToLoad = Math.min(this.totalFrames, this.maxWatchFrames);
        
        while (loadedFrames < maxFramesToLoad) {
            const start = loadedFrames;
            const end = Math.min(start + batchSize, maxFramesToLoad);
            
            try {
                // 使用CDN URL（如果启用）
                let apiUrl = this.useCDN ? `${this.cdnBaseUrl}/api/video/${filename}/frames/${start}/${end}` : `/api/video/${filename}/frames/${start}/${end}`;
                
                const response = await fetch(apiUrl);
                const data = await response.json();
                
                if (data.error) {
                    if (data.limit_reached) {
                        // 达到观看限制
                        this.watchLimitReached = true;
                        this.showMessage(data.error);
                        break;
                    }
                    throw new Error(data.error);
                }
                
                // 创建Image对象加载帧数据
                const loadPromises = data.frames.map(frame => {
                    return new Promise((resolve, reject) => {
                        const img = new Image();
                        img.onload = () => {
                            // 设置帧尺寸属性
                            img.width = frame.width;
                            img.height = frame.height;
                            img.frameIdx = frame.frame_idx;
                            img.frameData = frame;
                            console.log('帧加载成功:', frame.frame_idx, '尺寸:', frame.width, 'x', frame.height);
                            resolve(img);
                        };
                        img.onerror = () => {
                            console.error('帧加载失败:', frame.frame_idx);
                            reject(new Error('加载帧失败'));
                        };
                        img.src = frame.frame_data;
                    });
                });
                
                const frameImages = await Promise.all(loadPromises);
                this.frames.push(...frameImages);
                loadedFrames += frameImages.length;
                
                // 更新加载进度
                const progress = Math.round((loadedFrames / maxFramesToLoad) * 100);
                this.showMessage(`正在加载帧: ${loadedFrames}/${maxFramesToLoad} (${progress}%)`);
                
                // 检查观看限制
                if (data.watch_limit && !data.watch_limit.can_watch) {
                    this.watchLimitReached = true;
                    break;
                }
                
            } catch (error) {
                console.error('加载帧失败:', error);
                throw error;
            }
        }
        
        // 按帧索引排序
        this.frames.sort((a, b) => a.frameIdx - b.frameIdx);
    }
    
    loadStandardVideo() {
        if (!this.standardVideo) return;
        
        this.isBanFormat = false;
        this.standardVideo.currentTime = 0;
        this.hideLoading();
        this.renderFrame();
    }
    
    renderFrame() {
        if (this.isBanFormat) {
            this.renderBanFrame();
        } else {
            this.renderStandardFrame();
        }
    }
    
    renderBanFrame() {
        if (this.frames.length > 0 && this.currentFrame < this.frames.length) {
            const frame = this.frames[this.currentFrame];
            
            console.log('渲染帧:', this.currentFrame, '帧数据:', {
                hasFrame: !!frame,
                width: frame.width,
                height: frame.height,
                complete: frame.complete,
                naturalWidth: frame.naturalWidth,
                naturalHeight: frame.naturalHeight
            });
            
            // 使用natural尺寸
            const width = frame.naturalWidth || frame.width || 2932;
            const height = frame.naturalHeight || frame.height || 800;
            
            // 调整 canvas 尺寸以匹配帧（这会重置context）
            if (this.canvas.width !== width || this.canvas.height !== height) {
                console.log('调整Canvas尺寸:', width, 'x', height);
                this.canvas.width = width;
                this.canvas.height = height;
                // 尺寸改变后需要重新获取context
                this.ctx = this.canvas.getContext('2d');
            }
            
            // 确保图像已加载完成
            if (frame.complete || frame.naturalWidth > 0) {
                // 清除画布
                this.ctx.fillStyle = '#000';
                this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
                // 绘制帧
                this.ctx.drawImage(frame, 0, 0, width, height);
                console.log('成功绘制帧到Canvas:', width, 'x', height);
            } else {
                console.log('图像尚未加载完成，等待...');
                frame.onload = () => {
                    // 清除画布
                    this.ctx.fillStyle = '#000';
                    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
                    // 绘制帧
                    this.ctx.drawImage(frame, 0, 0, width, height);
                    console.log('图像加载完成后绘制帧:', width, 'x', height);
                };
            }
        } else {
            console.log('无帧数据，显示占位符');
            // 显示占位帧
            this.ctx.fillStyle = '#000';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.fillStyle = '#FF69B4';
            this.ctx.font = 'bold 24px Arial';
            this.ctx.textAlign = 'center';
            this.ctx.fillText('Banana Player', this.canvas.width / 2, this.canvas.height / 2 - 20);
            
            this.ctx.font = '16px Arial';
            this.ctx.fillStyle = '#FFB6D9';
            this.ctx.fillText('.ban 格式视频', this.canvas.width / 2, this.canvas.height / 2 + 20);
        }
    }
    
    renderStandardFrame() {
        if (this.standardVideo) {
            this.ctx.drawImage(this.standardVideo, 0, 0, this.canvas.width, this.canvas.height);
        }
    }
    
    play() {
        if (this.isBanFormat) {
            this.playBanVideo();
        } else {
            this.playStandardVideo();
        }
    }
    
    playBanVideo() {
        if (this.frames.length === 0) {
            this.showMessage('视频正在加载中...');
            return;
        }
        
        this.isPlaying = true;
        this.updatePlayButton();
        this.lastFrameTime = performance.now();
        this.animateBanVideo();
    }
    
    animateBanVideo() {
        if (!this.isPlaying) return;
        
        const now = performance.now();
        const elapsed = now - this.lastFrameTime;
        
        if (elapsed >= this.frameInterval) {
            this.currentFrame++;
            
            // 检查15秒限制
            if (this.currentFrame >= this.maxWatchFrames) {
                this.pause();
                this.watchLimitReached = true;
                this.showWatchLimitDialog();
                return;
            }
            
            if (this.currentFrame >= this.totalFrames) {
                this.currentFrame = 0;
            }
            
            this.renderBanFrame();
            this.updateProgress();
            this.updateTimeDisplay();
            this.lastFrameTime = now;
        }
        
        this.animationId = requestAnimationFrame(() => this.animateBanVideo());
    }
    
    pause() {
        this.isPlaying = false;
        this.updatePlayButton();
        
        if (this.isBanFormat) {
            cancelAnimationFrame(this.animationId);
        } else {
            this.standardVideo.pause();
        }
    }
    
    playStandardVideo() {
        if (this.standardVideo) {
            this.standardVideo.play();
        }
    }
    
    togglePlay() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    seek(percent) {
        if (this.isBanFormat) {
            this.currentFrame = Math.floor(percent * this.totalFrames);
            this.currentFrame = Math.max(0, Math.min(this.currentFrame, this.totalFrames - 1));
            this.renderBanFrame();
            this.updateProgress();
            this.updateTimeDisplay();
        } else {
            if (this.standardVideo) {
                this.standardVideo.currentTime = percent * this.standardVideo.duration;
            }
        }
    }
    
    nextFrame() {
        if (this.isBanFormat) {
            this.currentFrame++;
            if (this.currentFrame >= this.totalFrames) {
                this.currentFrame = 0;
            }
            this.renderBanFrame();
            this.updateProgress();
            this.updateTimeDisplay();
        } else {
            if (this.standardVideo) {
                this.standardVideo.currentTime += 1 / this.fps;
            }
        }
    }
    
    prevFrame() {
        if (this.isBanFormat) {
            this.currentFrame--;
            if (this.currentFrame < 0) {
                this.currentFrame = this.totalFrames - 1;
            }
            this.renderBanFrame();
            this.updateProgress();
            this.updateTimeDisplay();
        } else {
            if (this.standardVideo) {
                this.standardVideo.currentTime -= 1 / this.fps;
            }
        }
    }
    
    setVolume(value) {
        this.volume = value / 100;
        
        if (this.standardVideo) {
            this.standardVideo.volume = this.volume;
        }
        
        this.updateVolumeIcon();
    }
    
    toggleMute() {
        this.isMuted = !this.isMuted;
        
        if (this.standardVideo) {
            this.standardVideo.muted = this.isMuted;
        }
        
        this.updateVolumeIcon();
    }
    
    fullscreen() {
        if (this.container.requestFullscreen) {
            this.container.requestFullscreen();
        } else if (this.container.webkitRequestFullscreen) {
            this.container.webkitRequestFullscreen();
        }
    }
    
    updatePlayButton() {
        const playBtn = document.getElementById('play-btn');
        if (playBtn) {
            const icon = playBtn.querySelector('.play-icon');
            if (icon) {
                icon.textContent = this.isPlaying ? '⏸' : '▶';
            }
        }
    }
    
    updateProgress() {
        const progressFill = document.getElementById('progress-fill');
        if (progressFill) {
            let percent = 0;
            
            if (this.isBanFormat) {
                percent = this.totalFrames > 0 ? (this.currentFrame / this.totalFrames) * 100 : 0;
            } else if (this.standardVideo) {
                percent = (this.standardVideo.currentTime / this.standardVideo.duration) * 100 || 0;
            }
            
            progressFill.style.width = `${percent}%`;
        }
    }
    
    updateTimeDisplay() {
        const timeDisplay = document.getElementById('time-display');
        if (timeDisplay) {
            let current, total;
            
            if (this.isBanFormat) {
                current = this.currentFrame / this.fps;
                total = this.totalFrames / this.fps;
            } else if (this.standardVideo) {
                current = this.standardVideo.currentTime || 0;
                total = this.standardVideo.duration || 0;
            }
            
            timeDisplay.textContent = `${this.formatTime(current)} / ${this.formatTime(total)}`;
        }
    }
    
    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    updateVolumeIcon() {
        const muteBtn = document.getElementById('mute-btn');
        if (muteBtn) {
            const icon = muteBtn.querySelector('.volume-icon');
            if (icon) {
                if (this.isMuted || this.volume === 0) {
                    icon.textContent = '🔇';
                } else if (this.volume < 0.5) {
                    icon.textContent = '🔉';
                } else {
                    icon.textContent = '🔊';
                }
            }
        }
    }
    
    showLoading() {
        this.container.innerHTML = `
            <div class="player-placeholder">
                <div class="loading-spinner"></div>
                <p>正在加载视频...</p>
            </div>
        `;
    }
    
    showError(message) {
        this.container.innerHTML = `
            <div class="player-placeholder">
                <p style="color: #FF1493;">错误: ${message}</p>
            </div>
        `;
    }
    
    showMessage(message) {
        // 临时显示消息
        const existing = this.container.querySelector('.player-message');
        if (existing) {
            existing.remove();
        }
        
        const msg = document.createElement('div');
        msg.className = 'player-message';
        msg.style.cssText = 'position: absolute; bottom: 60px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.7); color: white; padding: 10px 20px; border-radius: 8px;';
        msg.textContent = message;
        this.container.appendChild(msg);
        
        setTimeout(() => msg.remove(), 3000);
    }
    
    showWatchLimitWarning() {
        // 显示15秒限制警告
        const warning = document.createElement('div');
        warning.className = 'watch-limit-warning';
        warning.style.cssText = 'position: absolute; top: 10px; right: 10px; background: rgba(255, 107, 107, 0.9); color: white; padding: 8px 12px; border-radius: 6px; font-size: 12px; z-index: 1000;';
        warning.innerHTML = '⚠️ 非会员用户仅可观看15秒';
        this.container.appendChild(warning);
        
        // 5秒后自动消失
        setTimeout(() => {
            if (warning.parentNode) {
                warning.remove();
            }
        }, 5000);
    }
    
    showWatchLimitDialog() {
        // 显示观看限制对话框
        const dialog = document.createElement('div');
        dialog.className = 'watch-limit-dialog';
        dialog.style.cssText = 'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: linear-gradient(135deg, #ff69b4, #ff1493); color: white; padding: 30px; border-radius: 15px; text-align: center; z-index: 2000; box-shadow: 0 10px 30px rgba(0,0,0,0.3);';
        dialog.innerHTML = `
            <h3 style="margin: 0 0 15px 0; font-size: 20px;">⏰ 观看时间到</h3>
            <p style="margin: 0 0 20px 0; font-size: 14px;">非会员用户只能观看15秒</p>
            <p style="margin: 0 0 25px 0; font-size: 12px; opacity: 0.9;">升级会员解锁完整功能</p>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button onclick="this.parentElement.parentElement.remove()" style="background: rgba(255,255,255,0.2); border: 1px solid rgba(255,255,255,0.3); color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer;">关闭</button>
                <button onclick="window.location.href='/upgrade'" style="background: white; color: #ff1493; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: bold;">升级会员</button>
            </div>
        `;
        this.container.appendChild(dialog);
    }
    
    hideLoading() {
        const placeholder = this.container.querySelector('.player-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        // 确保 canvas 存在
        if (!this.canvas) {
            this.canvas = document.createElement('canvas');
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            this.canvas.style.display = 'block';
            this.container.appendChild(this.canvas);
            this.ctx = this.canvas.getContext('2d');
            
            // 设置初始尺寸避免0x0问题
            this.canvas.width = 854;
            this.canvas.height = 480;
            this.ctx.fillStyle = '#000';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
            
            console.log('Canvas已创建，初始尺寸:', this.canvas.width, 'x', this.canvas.height);
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 检查是否是播放页面
    const player = document.getElementById('video-player');
    if (player && window.videoConfig) {
        const bananaPlayer = new BananaPlayer('video-player');
        
        // 设置播放器引用到全局
        window.bananaPlayer = bananaPlayer;
        
        // 根据视频类型加载
        if (window.videoConfig.isBanFormat) {
            bananaPlayer.loadBanVideo(window.videoConfig.filename);
        } else {
            bananaPlayer.loadStandardVideo();
        }
        
        // 绑定控制按钮事件
        bindControlEvents(bananaPlayer);
    }
});

function bindControlEvents(player) {
    // 播放/暂停按钮
    const playBtn = document.getElementById('play-btn');
    if (playBtn) {
        playBtn.addEventListener('click', () => player.togglePlay());
    }
    
    // 上一帧按钮
    const prevBtn = document.getElementById('prev-btn');
    if (prevBtn) {
        prevBtn.addEventListener('click', () => player.prevFrame());
    }
    
    // 下一帧按钮
    const nextBtn = document.getElementById('next-btn');
    if (nextBtn) {
        nextBtn.addEventListener('click', () => player.nextFrame());
    }
    
    // 静音按钮
    const muteBtn = document.getElementById('mute-btn');
    if (muteBtn) {
        muteBtn.addEventListener('click', () => player.toggleMute());
    }
    
    // 音量滑块
    const volumeSlider = document.getElementById('volume-slider');
    if (volumeSlider) {
        volumeSlider.addEventListener('input', (e) => player.setVolume(e.target.value));
    }
    
    // 进度条
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.addEventListener('click', (e) => {
            const rect = progressBar.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            player.seek(percent);
        });
    }
    
    // 全屏按钮
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', () => player.fullscreen());
    }
    
    // 分享按钮
    const shareBtn = document.getElementById('share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            const url = window.location.href;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(url).then(() => {
                    alert('链接已复制到剪贴板！');
                });
            } else {
                prompt('复制以下链接:', url);
            }
        });
    }
    
    // 键盘控制
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return;
        
        switch (e.key) {
            case ' ':
            case 'k':
                e.preventDefault();
                player.togglePlay();
                break;
            case 'ArrowLeft':
                player.prevFrame();
                break;
            case 'ArrowRight':
                player.nextFrame();
                break;
            case 'm':
                player.toggleMute();
                break;
            case 'f':
                player.fullscreen();
                break;
        }
    });
}
