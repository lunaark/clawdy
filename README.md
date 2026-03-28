# Clawdy 🦀

[English](#english) | [中文](#中文)

---

## English

A pixel-art desktop pet crab for macOS — your coding companion while waiting for Claude.

Clawdy is based on Claude's official mascot Clawd. While Claude is working, watch your little crab buddy do its thing — it makes the wait actually fun.

### Quick Start

```bash
python3 ~/animation/clawd_pet.py
```

Supports auto-launch on boot via LaunchAgent.

### Controls

| Action | How |
|--------|-----|
| Drag | Left-click and hold |
| Menu | Right-click / Control+click |
| Play music | Menu → 🎵 Play Music |
| Next track | Menu → ⏭ Next |
| Fireworks | Menu → 🎆 Fireworks |
| Quit | Menu → Quit |

### Animation States

#### Idle States (random auto-switch)

| State | Description |
|-------|-------------|
| idle | Breathing quietly + occasional blink |
| walk_left / walk_right | Walking sideways, window actually moves |
| dance | Swaying + raising claws + blush + foot particles |
| sleep | Curled up + floating Zzz |
| wave | Waving + heart particles |
| jump | Crouch → jump → bounce + particles |
| working | Coding at a tiny screen + sweating |
| happy | Bouncing + raising claws + floating hearts |
| eating | Find cookie → bite → crumbs → satisfied |
| excited | Fast bouncing + sparkle particles |
| firework | Light fuse → launch → Claude logo burst → afterglow |

#### Claude Code Integration

When you're using Claude Code, Clawdy reflects the work status in real time:

| State | Trigger |
|-------|---------|
| thinking | When you send a prompt — thought bubble |
| cc_working | When tools are called — coding at screen |
| error | When a tool fails — shaking + smoke |
| celebrate | When task completes — blush + particles |

#### Companion Awareness

| Behavior | Trigger |
|----------|---------|
| Tilts head at you | Mouse idle for 2 minutes |
| "Drink water" sign | After 45 minutes of continuous work |

### Eye Tracking

Clawdy's eyes follow your mouse cursor, with a 40px dead zone to prevent jitter.

### Music

Comes with 3 built-in lo-fi tracks. You can add more audio files to the `music/` folder:
- Formats: mp3, m4a, wav, aac, flac
- Auto-shuffle, auto-play next
- Uses macOS built-in `afplay` — zero dependencies

### Tech Stack

- **Language**: Python 3 + tkinter
- **Pixel rendering**: Canvas rectangles, SCALE=6 (each logical pixel = 6×6 screen pixels)
- **Transparent window**: macOS `systemTransparent` + `overrideredirect`
- **Particle system**: Physics simulation (gravity, velocity, life, decay)
- **Easing**: ease_out, ease_in_out, lerp
- **State machine**: Random transitions, 3-8 seconds per state
- **Claude Code integration**: HTTP server (port 18900) + Claude Code hooks
- **Music**: subprocess calling afplay
- **Auto-launch**: ~/Library/LaunchAgents/com.clawd.pet.plist

### Auto-Launch Management

```bash
# Disable auto-launch
launchctl unload ~/Library/LaunchAgents/com.clawd.pet.plist

# Enable auto-launch
launchctl load ~/Library/LaunchAgents/com.clawd.pet.plist
```

---

## 中文

macOS 像素风桌面宠物螃蟹，在你等待 Claude 的时候陪你编程。

Clawdy 是基于 Claude 官方吉祥物 Clawd 的桌面小伙伴，等 Claude 干活的时候，看它在旁边忙忙碌碌，让等待变得有趣。

### 快速启动

```bash
python3 ~/animation/clawd_pet.py
```

已配置开机自启动（LaunchAgent），重启电脑会自动出现。

### 操作方式

| 操作 | 方法 |
|------|------|
| 拖动 | 鼠标左键按住拖 |
| 菜单 | 右键 / Control+点击 |
| 播放音乐 | 菜单 → 🎵 播放音乐 |
| 切歌 | 菜单 → ⏭ 下一首 |
| 放烟花 | 菜单 → 🎆 放烟花 |
| 退出 | 菜单 → 退出 |

### 动画状态

#### 日常状态（随机自动切换）

| 状态 | 描述 |
|------|------|
| idle | 安静呼吸 + 偶尔眨眼 |
| walk_left / walk_right | 横着走，窗口真的移动 |
| dance | 左右摇摆 + 举钳子 + 腮红 + 脚底粒子 |
| sleep | 缩成一团 + 飘浮 Zzz |
| wave | 挥手 + 爱心粒子 |
| jump | 蓄力压扁→起跳→落地弹跳 + 粒子 |
| working | 面对小屏幕写代码 + 冒汗 |
| happy | 弹跳 + 举双钳 + 飘浮爱心粒子 |
| eating | 发现饼干→一口口咬→掉碎屑→满足 |
| excited | 快速蹦跳 + 闪光粒子 |
| firework | 点燃→上升→Claude logo 米字形绽放→余韵→欢呼 |

#### Claude Code 联动状态

当你使用 Claude Code 时，小螃蟹会实时反映工作状态：

| 状态 | 触发时机 |
|------|----------|
| thinking | 发送 prompt 时，头顶思考气泡 |
| cc_working | 调用工具时，面对屏幕写代码 |
| error | 工具报错时，身体颤抖 + 冒烟 |
| celebrate | 任务完成时，腮红 + 粒子庆祝 |

#### 小伙伴关心

| 行为 | 触发条件 |
|------|----------|
| 歪头看你 | 鼠标 2 分钟没动，它会抬头看你 |
| 喝水提醒 | 连续工作 45 分钟，头顶举起"喝水"小牌子 |

### 眼睛跟随

小螃蟹的眼睛会跟随鼠标方向看，有 40px 死区阈值避免抖动。

### 音乐播放

内置 3 首轻音乐，开箱可用。也可以把更多音频文件放到 `music/` 文件夹：
- 支持格式：mp3、m4a、wav、aac、flac
- 自动随机播放，播完自动下一首
- 使用 macOS 自带 afplay，零依赖

### 技术架构

- **语言**：Python 3 + tkinter
- **像素绘制**：Canvas rectangles，SCALE=6（每个逻辑像素 6×6 屏幕像素）
- **透明窗口**：macOS `systemTransparent` + `overrideredirect`
- **粒子系统**：物理模拟（重力、速度、生命周期、衰减）
- **缓动函数**：ease_out、ease_in_out、lerp
- **动画状态机**：随机切换，每种状态 3-8 秒
- **Claude Code 联动**：HTTP server（port 18900）+ Claude Code hooks
- **音乐**：subprocess 调用 afplay
- **开机自启**：~/Library/LaunchAgents/com.clawd.pet.plist

### 开机自启动管理

```bash
# 取消开机自启
launchctl unload ~/Library/LaunchAgents/com.clawd.pet.plist

# 恢复开机自启
launchctl load ~/Library/LaunchAgents/com.clawd.pet.plist
```

---

## File Structure

```
~/animation/
├── clawd_pet.py          # Main program
├── music/                # Music folder (3 built-in tracks)
│   └── *.mp3
├── dancing-clawd.html    # Clawd dancing animation
├── sunset-beach.html     # Sunset beach animation
└── README.md
```
