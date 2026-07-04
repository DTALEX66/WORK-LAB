# Migration Status｜迁移到 OPEN-DESIGN-Assistance

## 当前主目录

```text
D:\All projects\OPEN-DESIGN-Assistance
```

## 当前云端仓库

```text
https://github.com/DTALEX66/OPEN-DESIGN-Assistance
```

## 迁移状态

```text
已完成：Design-system → design-system/
已完成：MINIGAME → minigame-runtime/
已完成：Open Design 增强层骨架 → opendesign-assistance/
已完成：吸收与迁移记录 → project-memory/
已完成：Open Design 默认项目位置 → OPEN-DESIGN-Assistance
```

## 新目录是唯一主入口

从现在开始，和 Open Design 增强、MINIGAME 设计系统、游戏运行样板、提示词、Schema/Tokens、视觉验收相关的工作，默认都在：

```text
D:\All projects\OPEN-DESIGN-Assistance
```

旧目录仅作为历史来源/临时备份，不再作为主开发入口：

```text
D:\All projects\Design-system
D:\All projects\MINIGAME
```

## 新目录内的职责

```text
design-system/             Open Design-first 设计系统与 Design Command Center
minigame-runtime/          原 MINIGAME 游戏生产系统运行样板
opendesign-assistance/     Open Design 增强层：prompts / adapters / templates / workflows
project-memory/            吸收、迁移、决策、边界记录
```

## 注意

- 不直接删除旧目录，除非用户明确要求。
- 不再从旧目录继续开发新功能。
- 如果旧目录后续出现新改动，需要先判断是否同步吸收到本主仓。
- Open Design 主窗口设计以 Open Design 为主；外部 Figma 仅作协作/导入导出/精修备选。
