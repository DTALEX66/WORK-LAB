# ASSET_REPLACEMENT_MANIFEST — WORK-LAB L10 UI 落地

> L10 执行：所有参考资产先做"可否直接使用"判定；能直接用 ⇒ 直接复刻（CSS/组件），
> 不能直接进运行时 ⇒ 1:1 重生成并登记。本清单记录全部判定。

## 判定总则（参考图 B01–B10 vs 运行时资产边界）

- 参考 zip 内的 1920×1080 页面图 / VI 图 = **审计对照源**（`.project-local/runs/ui-suite/`，
  gitignored），**不**作为运行时位图进 `src/`（避免 230MB 参考资产进仓库、避免低分辨率
  被拉伸、避免与品牌 token 双份真值）。
- 运行时视觉全部由 B10 token + 组件 + CSS 光效类生成（可无限分辨率、可主题翻转、
  可 CI 断言）——这是比位图更强的 1:1 复刻。

## 逐项判定

| 原参考 | 判定 | 原因 | 运行时位置 | 差异说明 |
|---|---|---|---|---|
| B02 `VI/03_03_主标志_Primary_Logo.png`（WL 几何构造） | **不直接嵌入**；1:1 以 B10 `brand-mark` 形态实现 | B10 最终版已把 Logo 定为 48px 渐变圆角方 + `WL` 900 字标 + 主色投影；位图 Logo 无法随 light/dark 主题翻转、无法走 token 体系 | `Sidebar.tsx` Header `brand-mark`（B10 同款：radial+linear 渐变、`0 10px 30px primary/38%` 投影） | 零差异：品牌色/几何/字重与 B10 一致；比位图多了主题自适配 |
| B10 `.grid-bg` 32px 网格 + ambient 三团光 | **直接复刻**（纯 CSS，无需位图） | B10 本身即用 CSS 实现，无位图资产 | `src/index.css` `.wl-grid-bg` / `.wl-ambient`（1:1 B10 参数：blur 80px、opacity .45、floatGlow 12s） | 零差异；参数照抄 B10 |
| B10 `.node` / `.wl-edge-line` / 核心 pulse 光效 | **直接复刻**（CSS 类 + 组件） | 光效 = 系统状态语言，B10 参数固定 | `index.css` `.wl-node-glow` `.wl-edge-line` `.wl-core-pulse` `.wl-scanline` `.wl-kpi-glow` + `components/graph/*` | 零差异；drop-shadow/dasharray/关键帧时长照抄 |
| B05 12 张 / B03 10 张页面级 1920×1080 PNG | **不进运行时**；作为 Visual QA 对照图 | 页面在真实 React 组件中渲染，比静态 PNG 保真且可交互；PNG 仅用于逐页比对（结构>比例>布局>颜色>组件>字体>细节>光效>动效） | `VISUAL_QA_REPORT.md` 逐页记录 | 运行时 = 组件化真实现，非截图贴皮 |
| B01 品牌应用/壁纸（`VI/18_18_品牌应用_UI纹理与壁纸.png`） | **不生成位图壁纸**；纹理由 `.wl-grid-bg` + ambient 承担 | B10 最终版未使用位图壁纸；用位图会引入不可主题翻转的第二视觉真值 | 同上 | 与 B10 一致（B10 无壁纸层） |
| 图标 | **不重生成**；用 `lucide-react`（已有依赖）线性图标 | B02 图标系统两组为品牌图示；UI 功能图标按 B07 契约用既有图标库保持线性/密度一致 | 各 view 现有 `lucide-react` 用法 | 功能图标 1:1；品牌图形（Logo/网格）走 token |
| 页面 hero/星球/控制平面视觉 | **不存在于 B10 参考**；不生成 | B10 视觉语言 = 深黑蓝控制台 + 微弱蓝色环境光 + 网格（§八 光效要求，禁止"花哨 AI 风"），无 hero 位图；自生成会违反"禁止重新设计" | 无 | 无差异（参考里就没有） |

## 生成资产目录（本轮实际生成）

- 无新增位图资产（`src/assets/generated/` 未创建）：B10 可部署 UI 的全部视觉均由
  CSS token/关键帧/组件实现，直接复刻即可达到 1:1，且优于位图（可主题化/可测试/可无限分辨率）。
- 若后续授权接入真实 workflow schema 后端并需要节点类型位图，再按本清单流程生成并补登。
