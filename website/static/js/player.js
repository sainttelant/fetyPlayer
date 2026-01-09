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
        // 创建 canvas 元素
        this.canvas = document.createElement('canvas');
        this.canvas.width = 854;
        this.canvas.height = 480;
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.objectFit = 'contain';
        this.container.innerHTML = '';
        this.container.appendChild(this.canvas);
        
        this.ctx = this.canvas.getContext('2d');
        
        // 隐藏占位符
        const placeholder = this.container.querySelector('.player-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
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
        
        try {
            this.showLoading();
            
            // 获取视频信息
            const infoResponse = await fetch(`/api/video/${filename}/info`);
            const infoData = await infoResponse.json();
            
            if (infoData.error) {
                throw new Error(infoData.error);
            }
            
            this.fps = infoData.info.fps || 30;
            this.totalFrames = infoData.info.frame_count || 0;
            this.frameInterval = 1000 / this.fps;
            
            // 解码视频
            await this.decodeBanVideo(filename);
            
            this.hideLoading();
            this.renderFrame();
            this.updateTimeDisplay();
            
        } catch (error) {
            console.error('加载视频失败:', error);
            this.showError(error.message);
        }
    }
    
    async decodeBanVideo(filename) {
        // 获取视频数据块
        const response = await fetch(`/videos/${filename}`);
        const blob = await response.blob();
        const arrayBuffer = await blob.arrayBuffer();
        
        // 这里需要后端支持分块传输帧数据
        // 简化版本：使用 API 获取帧数据
        // 实际实现需要后端提供帧解密 API
        
        // 模拟加载帧数据
        this.frames = [];
        this.showLoading();
        
        // 注意：完整实现需要后端提供帧解密端点
        // 这里显示提示信息
        this.showMessage('正在准备播放 .ban 格式视频...');
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
            
            // 调整 canvas 尺寸以匹配帧
            if (this.canvas.width !== frame.width || this.canvas.height !== frame.height) {
                this.canvas.width = frame.width;
                this.canvas.height = frame.height;
            }
            
            this.ctx.putImageData(frame, 0, 0);
        } else {
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
    
    hideLoading() {
        const placeholder = this.container.querySelector('.player-placeholder');
        if (placeholder) {
            placeholder.style.display = 'none';
        }
        
        // 确保 canvas 存在
        if (!this.canvas) {
            this.canvas = document.createElement('canvas');
            this.canvas.width = 854;
            this.canvas.height = 480;
            this.canvas.style.width = '100%';
            this.canvas.style.height = '100%';
            this.container.appendChild(this.canvas);
            this.ctx = this.canvas.getContext('2d');
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
