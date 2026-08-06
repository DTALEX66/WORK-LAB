# Open-source absorption candidates

Purpose: track open-source plugins, skills, DESIGN.md systems, and templates that can strengthen Open Design through this assistance repo without vendoring large upstream repositories.

## Rules

- Absorb capability patterns, prompt structure, QA gates, template taxonomy, and references first.
- Do not bulk-copy third-party repos or generated media.
- Keep source attribution and license notes.
- Prefer small Markdown templates under `opendesign-assistance/templates/`.
- Promote only proven patterns into Open Design plugins.

## P0: absorb now

| Source | License observed | Why it matters | Absorb as |
|---|---:|---|---|
| `nexu-io/open-design` official `plugins/spec` and docs | project upstream | canonical plugin shape, publishing, registry, install flow | plugin install/publishing notes, plugin scaffold conventions |
| `nexu-io/open-design` `design-templates` | project upstream | dashboard, SaaS landing, mobile, poster, critique, deck templates | local layout/graphic/deck template taxonomy |
| `Nutlope/hallmark` | MIT | anti-AI-slop design gates, theme variation, pre-emit self-critique | `templates/qa/anti-ai-slop-checklist.md` |
| `VoltAgent/awesome-design-md` | MIT | brand DESIGN.md references for developer/SaaS UI | style reference index, future DESIGN.md refs |
| `dominikmartn/nothing-design-skill` | MIT | monochrome industrial UI, dot matrix, mechanical controls | HUD/console rules, dark industrial variants |

## P1: absorb next

| Source | License observed | Why it matters | Absorb as |
|---|---:|---|---|
| `JimLiu/baoyu-design` | MIT | portable high-fidelity HTML design skill; mockups, dashboards, decks | prototype/deck generation workflow |
| `bitjaru/styleseed` | MIT | design judgment, brand skins, component and motion rules | component-patterns and motion templates |
| `hamen/material-3-skill` | MIT | Material 3 tokens/components/audit | standard UI component checklist |
| `google-labs-code/stitch-skills` | Apache-2.0 | Agent Skills open structure and marketplace patterns | agent skill compatibility note |
| `kzhrknt/awesome-design-md-jp` | MIT | CJK typography and line-breaking rules | `templates/typography/cjk-ui-typography.md` |

## P2: later

| Source | Why later | Possible local output |
|---|---|---|
| `m-roberts/deploy-to-cloudflare-pages` | side-effecting publishing flow; needs confirmation UX | `plugins/deploy-preview/` |
| `VaqueroGroup/reusable-workflow-author` | useful scaffold idea but needs local validation | `scripts/scaffold_open_design_plugin.py` |
| `lefarcen/pitch-deck-bootstrap` | deck-focused; lower priority than UI/UX now | `templates/decks/pitch-deck.md` |
| `lefarcen/brief-to-slide-outline` | content structuring; can follow deck work | brief-to-outline template |
| `dominikmartn/hue` | brand extraction may need website/screenshot tooling | `plugins/brand-to-design-system/` |

## First absorption batch landed locally

```text
opendesign-assistance/templates/qa/anti-ai-slop-checklist.md
opendesign-assistance/templates/layouts/landing-page.md
opendesign-assistance/templates/layouts/dashboard.md
opendesign-assistance/templates/layouts/mobile-menu.md
opendesign-assistance/templates/layouts/settings-panel.md
opendesign-assistance/templates/layouts/pricing-page.md
opendesign-assistance/templates/layouts/product-page.md
opendesign-assistance/templates/graphic/poster-cover.md
opendesign-assistance/templates/graphic/social-card.md
opendesign-assistance/templates/decks/pitch-deck.md
opendesign-assistance/templates/motion/motion-system.md
opendesign-assistance/templates/brand/brand-identity-system.md
opendesign-assistance/templates/spatial/culture-wall.md
opendesign-assistance/templates/spatial/exhibition-hall.md
opendesign-assistance/templates/visual/art-direction.md
opendesign-assistance/templates/visual/2d-design.md
opendesign-assistance/templates/visual/3d-design.md
opendesign-assistance/templates/typography/cjk-ui-typography.md
opendesign-assistance/templates/design-systems/style-reference-index.md
```

These templates intentionally encode reusable design judgment rather than third-party code.

## 2026-08-06 read-only source verification

本节只记录公开 GitHub 元数据与 WORK-LAB 本地目标路径核对；没有 clone、vendor、运行第三方 Skill 或读取任何凭据。完整机器可读证据保存在项目忽略目录 `.hermes/task-artifacts/`。

| Source | Verified license | Verified default-branch HEAD | Local mapping status | Next action |
|---|---|---|---|---|
| `nexu-io/open-design` | Apache-2.0 | `5a2e5610…` | plugin workspace/research present | 继续按官方 plugin schema 做结构核对 |
| `Nutlope/hallmark` | MIT | `0a0f706b…` | anti-AI-slop checklist present | 仅做内容/归因复核 |
| `VoltAgent/awesome-design-md` | MIT | `8147538b…` | style-reference index present | 复核引用边界，不复制整仓 |
| `dominikmartn/nothing-design-skill` | MIT | `74affbb7…` | anomaly-monitor design-system present | 做风格规则归因复核 |
| `JimLiu/baoyu-design` | MIT | `026d4ea0…` | template family present | 按模板能力逐项验证 |
| `bitjaru/styleseed` | MIT | `e0a09915…` | templates/design-systems present | 补 token/motion 对照验证 |
| `hamen/material-3-skill` | MIT | `14385f2b…` | no dedicated target; generic templates only | 新增前先定义 M3 checklist 边界 |
| `google-labs-code/stitch-skills` | Apache-2.0 | `535b0889…` | workflow skills/plugin workspaces exist | 做 Agent Skill compatibility review |
| `kzhrknt/awesome-design-md-jp` | MIT | `b95177a7…` | CJK typography template present | 内容归因复核 |
| `m-roberts/deploy-to-cloudflare-pages` | MIT | `c691d16d…` | no local target | 暂缓，涉及发布副作用 |
| `VaqueroGroup/reusable-workflow-author` | **未从 GitHub 元数据确认许可证** | `af2969a2…` | scaffold script exists | quarantine，不吸收源内容 |
| `lefarcen/pitch-deck-bootstrap` | **未从 GitHub 元数据确认许可证** | `306cb3d0…` | pitch-deck template exists | quarantine，只保留独立原创结构待复核 |
| `lefarcen/brief-to-slide-outline` | **未从 GitHub 元数据确认许可证** | `a9a288b1…` | no dedicated target | quarantine，不复制 |
| `dominikmartn/hue` | MIT | `a910e31c…` | no local target | 后续再做 brand-to-design-system 设计，不先运行 |

当前结论：已有本地文件的候选只能标记为“模式已落地/结构存在”，不能标记为“按当前 upstream 版本完整吸收”。无许可证候选保持 quarantine；发布类候选保持 approval-gated。

## Promotion path

1. Capture pattern as Markdown template.
2. Use it inside Open Design prompts/plugins.
3. Run `design-qa-critic` after generation.
4. If it repeatedly works, promote the pattern into a plugin SKILL.md.
5. If it becomes a full visual language, promote it into `design-systems/`.
