# MINIGAME 资产规则

## 去 AI 味儿背景图规则

- 背景图不允许带文字、logo、水印、可读招牌、伪 UI 字幕或随机乱码。
- CCTV / HUD / 控制台背景只能提供环境、材质、光影、噪声和镜头氛围。
- UI 文字必须由 HTML/Canvas 渲染，不能烘焙在 PNG/JPG/WebP/GIF 背景图里。
- 如果素材里出现 OCR 可读文字、AI 乱码、品牌标识或水印，必须退回重做或裁掉。
- `ui-reference-*` 只作为设计参考图，不允许作为游戏运行时背景图。

## 验收

1. CSS 运行时背景不得引用 `ui-reference-*`。
2. 新增背景/覆盖层资源文件名不得暗示 text / logo / watermark / caption / title 等烘焙文字用途。
3. 游戏内可读信息统一进入 DOM 节点、Canvas 绘制文本或皮肤 JSON 文案。

## Game001 CCTV 资产分层

- `cctv-elevator-corridor-clear.png`：正常巡检背景。
- `cctv-elevator-corridor-warp.png`：异常态背景，仅在 `data-anomaly="active"` 时切换。
- `cctv-elevator-corridor-figure.png`：critical / danger 异常背景。
- 以上三张图已去除源图右下角生成器水印；后续替换时必须重复水印/文字检查。
