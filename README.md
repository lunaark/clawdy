# Clawdy 🦀

macOS 像素风桌面宠物螃蟹，在你等待 Claude 的时候陪你编程。

Clawdy 是基于 Claude 官方吉祥物 Clawd 的桌面小伙伴，等 Claude 干活的时候，看它在旁边忙忙碌碌，让等待变得有趣。

## 快速启动

```bash
python3 ~/animation/clawd_pet.py
```

已配置开机自启动（LaunchAgent），重启电脑会自动出现。

## 操作方式

| 操作 | 方法 |
|------|------|
| 拖动 | 鼠标左键按住拖 |
| 菜单 | 右键 / Control+点击 |
| 播放音乐 | 菜单 → 🎵 播放音乐 |
| 切歌 | 菜单 → ⏭ 下一首 |
| 放烟花 | 菜单 → 🎆 放烟花 |
| 退出 | 菜单 → 退出 |

## 动画状态

### 日常状态（随机自动切换）

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

### Claude Code 联动状态

当你使用 Claude Code 时，小螃蟹会实时反映工作状态：

| 状态 | 触发时机 |
|------|----------|
| thinking | 发送 prompt 时 |
| cc_working | 调用工具时 |
| error | 工具报错时 |
| celebrate | 任务完成时 |

## 眼睛跟随

小螃蟹的眼睛会跟随鼠标方向看，有 40px 死区阈值避免抖动。

## 音乐播放

把音频文件放到 `~/animation/music/` 文件夹：
- 支持格式：mp3、m4a、wav、aac、flac
- 自动随机播放，播完自动下一首
- 使用 macOS 自带 afplay，零依赖

## 技术架构

- **语言**：Python 3 + tkinter
- **像素绘制**：Canvas rectangles，SCALE=6（每个逻辑像素 6×6 屏幕像素）
- **透明窗口**：macOS `systemTransparent` + `overrideredirect`
- **粒子系统**：物理模拟（重力、速度、生命周期、衰减）
- **缓动函数**：ease_out、ease_in_out、lerp
- **动画状态机**：随机切换，每种状态 3-8 秒
- **Claude Code 联动**：HTTP server（port 18900）+ Claude Code hooks

- **音乐**：subprocess 调用 afplay
- **开机自启**：~/Library/LaunchAgents/com.clawd.pet.plist

## 文件结构

```
~/animation/
├── clawd_pet.py          # 桌面宠物主程序
├── music/                # 音乐文件夹
│   └── *.mp3
├── dancing-clawd.html    # Clawd 跳舞动画
├── sunset-beach.html     # 海边看日落动画
└── README.md


```

## 开机自启动管理

```bash
# 取消开机自启
launchctl unload ~/Library/LaunchAgents/com.clawd.pet.plist

# 恢复开机自启
launchctl load ~/Library/LaunchAgents/com.clawd.pet.plist
```
