# MINIGAME 游戏合集目录

本目录用于管理 MINIGAME 的游戏分类和每个游戏的本地 manifest。

MINIGAME 当前定位：**小游戏合集平台**。每个游戏不是孤立项目，而是平台上的一个可发布、可换皮、可复用生产链的内容单元。

## 分类

| 分类 | 目录 | 当前状态 |
|---|---|---|
| 找异常 | `find-anomaly/` | 已有首发游戏：异常电梯控制台 |
| 反应时机 | `timing-reflex/` | 规划中 |
| 轻解谜 | `puzzle-logic/` | 规划中 |
| 放置升级 | `idle-upgrade/` | 规划中 |
| 轻模拟经营 | `simulation-management/` | 规划中 |

## 当前已接入游戏

- `find-anomaly/elevator-console` — 找异常：异常电梯控制台

## 接入新游戏的最低要求

每个新游戏目录至少包含：

- `README.md`：玩家体验、玩法循环、广告点、目标平台
- `game.manifest.json`：稳定 ID、分类、入口、构建目标、广告点、内容包关系
- `runtime-map.md`：当前代码入口和资源映射
