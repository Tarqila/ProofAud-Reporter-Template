# ProofAud-Reporter-Template

把 Markdown 格式的智能合约审计内容，填充进 **Proof Audit** 品牌 HTML 模板，并渲染为 A4 尺寸的 PDF 报告。

这是一个"排版层"工具：**脚本负责拼接，Agent 负责行文，任何审计事实都不由脚本虚构。**

## 特性

- **A4 品牌版式**：7 个固定页 + 每个发现一页；双主题（暗色 · 海上明月 / 亮色 · 海上太阳）自由选用，两主题共用同一版式几何
- **确定性填充**：`report.json` → HTML，自动处理中英文版式、页码、目录重建、发现页克隆与行距自适应（常规 / tight / xt 三档）
- **可选增强块**：元信息行、影响分析表、证据链、说明框——让每条发现带上证据与可证伪的影响描述
- **未覆盖领域章节**：可选的「未覆盖区域与残余风险」独立章节，明确审计边界
- **署名固化**：Prepared By 与联系邮箱统一注入，封面 / 文档控制页 / 联系卡 / 页脚四处一致

## 目录结构

```
SKILL.md                            技能入口（流程 + 强制确认 + 硬规则）
assets/template/index.html          A4 双主题模板
scripts/fill_template.py            report.json → HTML（确定性填充）
scripts/render.sh                   导出 PDF（Chromium → Playwright 降级）
scripts/render_pw.js
references/mapping.md               report.json 完整 schema
references/author.md                署名与联系方式单一来源
proof-audit-report-builder.skill    打包分发件
CHANGE_LOG.md
```

## 快速开始

```bash
python3 scripts/fill_template.py report.json -o report.html
bash scripts/render.sh report.html "Project_Audit_Report.pdf"
```

schema 与 Markdown → JSON 转换规则详见 `references/mapping.md`。

## 可选字段速查

| 字段 | 渲染为 |
|---|---|
| `findings[].meta` | 元信息行（CWE、触发可能性等） |
| `findings[].impact_table` | 影响分析表（场景 → 影响，让影响可被证伪） |
| `findings[].evidence` | 证据链（带标签的代码块） |
| `findings[].note` | 说明框（记录"为何不是更高危"的降级理由） |
| `uncovered` | 独立章节「未覆盖区域与残余风险」+ 可选 checklist |

全部缺省时，输出与基础版式逐字一致；`uncovered` 出现时自动成为第 4 节、
免责声明顺延第 5 节，目录与页码由脚本自动重算。

## 署名与联系

**Sev7ero**

Sevzero402@gmail.com

本模板负责把已有的审计结论自动排版为报告，**它不替代人工审计**——
经济模型推演、闭源合约的黑盒验证、DApp 与后端安全等环节，仍需要人工判断。
如需人工审计或深度复核，可通过上方邮箱联系。

## 许可证（License）

保留所有权利（All Rights Reserved），自定义授权如下：

- **个人学习、研究、自用：免费，无需授权。**
- **任何商用平台的转载、集成、二次开发及盈利行为，必须：① 注明来源（本仓库链接）；② 事先获得商业授权。**

本声明旨在保留原作者版权与商业权利，防止代码被滥用。如需商业授权，请联系本人。

Copyright © 2026 nigel（GitHub: Tarqila）

---

*免责声明：使用本模板生成的报告仅反映审计时点的代码状态，不构成投资建议。*
