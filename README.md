# Zotero Local MCP: 纯本地 Zotero 论文管理与 AI 智能体连接器

<p align="center">
  <img src="https://img.shields.io/badge/Zotero-10%2B-CC2936?style=for-the-badge&logo=zotero&logoColor=white" alt="Zotero 10+">
  <img src="https://img.shields.io/badge/Protocol-MCP-0175C2?style=for-the-badge&logoColor=white" alt="MCP">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Storage-Local%20Only-2ea44f?style=for-the-badge" alt="Local Only">
  <img src="https://img.shields.io/badge/Release-v1.0.0-blue?style=for-the-badge" alt="Release">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

**Zotero Local MCP** 专为追求**零云端依赖**、**无存储容量限制**的学术研究者设计。通过 Zotero 10 原生本地 API（`http://localhost:23119/api/`），在本地构建完整的 Model Context Protocol (MCP) 服务与命令行工具 (`zotero-cli`)。

让 Claude Desktop、Cursor、Oh My Pi (OMP)、Windsurf 等 AI 编程智能体能够无缝检索、阅读、批注和管理您的本地文献库，同时**彻底切断向 Zotero 云端上传附件文件**，告别 300MB 云端存储配额限制。

---

## 🌟 核心特性与本地架构

### 1. 纯本机读写，零云端配额消耗 (Zero Cloud Storage)
- **附件直接本地落盘**：通过 DOI、URL、arXiv 或本地文件添加的 PDF 附件，由本机 Zotero 直接复制至本地 `storage/<attachment-key>/`，**完全不走 Zotero.org 云端存储**。
- **与 Zotero 桌面端 WebDAV 完美兼容**：文献在本地导入后，Zotero 桌面端会按您既有的 WebDAV 配置自行后台同步，MCP 不再直连 WebDAV，绝不破坏您现有的同步链路。

### 2. 原生本地授权 (Native Local Authorization)
- 基于 Zotero 10 的 `POST /api/local/authorize` 规范，只需一次性授权：
  ```bash
  pyzotero authorize --app-name "Zotero MCP Local"
  ```
- 在 Zotero 桌面端原生弹窗中选择 **Always Allow** 即可完成握手。本地 API Key 安全保存在本机 `~/.config/pyzotero/local-api-key.json`（权限 `0600`），**MCP 配置中不再需要明文暴露任何 API Key**。

### 3. 可逆安全删除 (Safe Trash Deletion)
- 论文、笔记与注释的删除全部调用底层 `PATCH {"deleted": 1}` 移入 **Zotero 回收站**，绝不调用不可逆的硬删除。误删条目在 Zotero 桌面端回收站中可随时一键恢复。

### 4. 代理穿透与防 502 保护 (Loopback Proxy-Safe)
- 针对国内科研网络环境普遍开启系统代理（如 Clash 7890 端口）导致本机请求误入代理返回 `502 Bad Gateway` 的顽疾，源码级强制绑定 `NO_PROXY=127.0.0.1,localhost`，确保本地通信绝对稳定。

### 5. 双轨运行支持 (MCP Server + CLI)
- **MCP 服务**：为各类支持 MCP 的 AI Agent 提供多达 30+ 项标准工具（检索、大纲、高亮、区域框选、集合转移、元数据管理）。
- **命令行界面 (`zotero-cli`)**：无需启动 AI 也能在终端快速检索、导入、转移、批注文献，全部支持 `--json` 输出，便于脚本批处理。

---

## 📋 功能全景

| 模块 | 核心能力 | MCP 工具 / CLI 命令 |
| :--- | :--- | :--- |
| **文献检索** | 快速关键词检索、高级多字段逻辑检索、跨库全域搜索（个人文库+群组）、布尔标签检索 | `zotero_search_items`<br>`zotero_advanced_search`<br>`zotero_search_by_tag` |
| **论文阅读** | PDF/EPUB 全文提取与 Markdown 转换、PDF 目录大纲/书签解析、按页码精准读取 | `zotero_get_item_fulltext`<br>`zotero_get_pdf_outline`<br>`zotero_read_pdf_pages` |
| **批注与笔记** | PDF 精准文本高亮、图形/表格区域截图框选 (Normalized Rect)、Markdown/HTML 笔记创建与追加 | `zotero_create_annotation`<br>`zotero_manage_note`<br>`zotero_get_annotations` |
| **本地文献录入** | 从 DOI、arXiv、URL、ISBN、BibTeX、CSL-JSON 或本地文件导入，自动抓取 OA PDF 并本地落盘 | `zotero_add_item`<br>`zotero_attach_file` |
| **集合与整理** | 创建/删除集合、论文在集合间平滑转移（支持同时加入与移出指定集合）、批量标签更新 | `zotero_set_item_collections`<br>`zotero_create_collection`<br>`zotero_batch_update` |
| **条目维护** | 条目移入回收站 (Trash)、更新字段元数据、重复文献扫描与合并 | `zotero_delete_item`<br>`zotero_update_item`<br>`zotero_duplicates` |

---

## 🚀 快速上手

### 1. 前置准备
1. 安装 **Zotero 10+**（可在 [Zotero 官网](https://www.zotero.org/download/) 下载最新版本）。
2. 打开 Zotero 设置：
   - macOS: `Settings (偏好设置)` → `Advanced (高级)` → 勾选 **“允许本机其他应用程序与 Zotero 通信” (Allow other applications on this computer to communicate with Zotero)**。
   - Windows/Linux: `Edit` → `Preferences` → `Advanced` → 勾选相同选项。

### 2. 安装与本地授权

推荐使用 [`uv`](https://docs.astral.sh/uv/) 工具安装：

```bash
# 1. 安装 zotero-local-mcp 工具
uv tool install --force git+https://github.com/JingYangYuan/zotero-local-mcp.git

# 2. 确保 Zotero 正在运行，执行本地授权
pyzotero authorize --app-name "Zotero MCP Local"
```

> **提示**：运行 `pyzotero authorize` 时，Zotero 桌面端会弹出授权对话框，请点击 **“Always Allow”**。授权密钥将安全写入 `~/.config/pyzotero/local-api-key.json`。

验证配置与授权状态：
```bash
zotero-cli --json config
```
输出显示 `ZOTERO_LOCAL: true` 且无报错即表示配置成功！

---

## ⚙️ MCP 客户端配置指南

### 1. Oh My Pi (OMP)
在 `~/.omp/agent/mcp.json` 中配置：

```json
{
  "mcpServers": {
    "zotero": {
      "type": "stdio",
      "command": "zotero-mcp-server",
      "args": ["serve"],
      "env": {
        "ZOTERO_LOCAL": "true",
        "ZOTERO_MCP_SCHEMA_REFRESH": "0"
      }
    }
  }
}
```

### 2. Claude Desktop
编辑 Claude Desktop 配置文件：
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "zotero": {
      "command": "zotero-mcp-server",
      "args": ["serve"],
      "env": {
        "ZOTERO_LOCAL": "true",
        "ZOTERO_MCP_SCHEMA_REFRESH": "0"
      }
    }
  }
}
```

### 3. Cursor
在 `.cursor/mcp.json` 或设置中添加：
```json
{
  "mcpServers": {
    "zotero": {
      "command": "zotero-mcp-server",
      "args": ["serve"],
      "env": {
        "ZOTERO_LOCAL": "true",
        "ZOTERO_MCP_SCHEMA_REFRESH": "0"
      }
    }
  }
}
```

---

## 💻 命令行 (`zotero-cli`) 常用场景速查

不需要 AI 交互时，`zotero-cli` 是极佳的文献管理终端工具：

```bash
# 1. 搜索文献（支持模糊、关键词与题名）
zotero-cli search "资源依赖理论"
zotero-cli --json search "制度理论" --limit 5

# 2. 查看文献详情与子附件
zotero-cli get metadata EKPGJJ9D
zotero-cli get children EKPGJJ9D

# 3. 添加文献（自动匹配 DOI 并下载 OA 论文至本地 storage）
zotero-cli add doi 10.1145/3708319
zotero-cli add file --filepath ~/Downloads/paper.pdf --title "重要论文"

# 4. 集合管理与论文分类转移
zotero-cli collections search "组织学"
zotero-cli collections manage --item-keys EKPGJJ9D --add-to NEW_COLL_KEY --remove-from OLD_COLL_KEY

# 5. 安全移入回收站
zotero-cli delete item EKPGJJ9D
```

---

## ❓ 常见问题 (FAQ)

#### Q1: 为什么完全不再需要 `ZOTERO_API_KEY` 和 `ZOTERO_LIBRARY_ID`？
**答**：在早期的混合 (Hybrid) 模式下，本地 API 仅支持只读，写操作必须经由官方云端 Web API 转发并消耗云端存储。Zotero 10 原生开放了本地授权与写入机制，所有条目增删改和附件落盘均直接在本地执行，因此不再需要配置 Zotero.org 凭据。

#### Q2: 本地添加的文献和 PDF 还会同步到其他设备吗？
**答**：会。只要您在 Zotero 桌面端设置中配置了 WebDAV（或开启了个人账号同步），通过本 MCP 添加的文件落盘到本地 `storage/` 后，Zotero 桌面端会自动检测并将附件同步至您的 WebDAV 服务器，完全无缝。

#### Q3: 误删了文献如何找回？
**答**：打开 Zotero 桌面端，在左侧侧边栏中点击 **“回收站” (Trash)**，找到对应的条目，右键选择 **“恢复到文库”** 即可完全复原文献条目及其附件。

---

## 📄 开源许可证

本项目基于 [MIT License](LICENSE) 开源。欢迎提交 Issue 与 Pull Request！
