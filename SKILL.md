---
name: proof-audit-report-builder
description: Turn a Markdown smart-contract audit report (findings, scope, methodology, appendices) into a finished Proof Audit branded HTML/PDF report. Use when the user provides audit content in .md form and asks to 填充/排版/生成 the Proof Audit 审计报告模板, produce the 双主题 (海上明月/海上太阳) report, or batch-convert audit findings into the branded layout.
version: 1.0.0
homepage: https://github.com/Tarqila/ProofAud-Reporter-Template
---

# Proof Audit Report Builder

Convert agent-supplied Markdown audit content into the fixed Proof Audit HTML
template (A4, dual theme), then render to PDF. The script does the splicing;
the agent does the prose. Never invent audit facts.

## Assets

- `assets/template/index.html` — the brand template (7 fixed pages + 1 page per
  finding). Do not edit its CSS or layout; only content is substituted.
  Typography (行距/页边距/页眉间距) is already tuned in the template — never
  append ad-hoc `<style>` overrides to generated reports.
- `scripts/fill_template.py` — deterministic filler: `report.json` → final HTML.
  Handles theme, **language (`lang`, default `zh`)**, finding-page cloning,
  TOC rebuild, page numbering, and optional header tip / contact column.
- `scripts/render.sh` — headless-Chromium PDF export + screenshot QA
  (chromium → chromium-browser → Playwright fallback).
- `references/mapping.md` — the full `report.json` schema, Markdown→JSON
  conversion rules, severity/status vocabularies, and the confirmation
  checklist. **Read it before building report.json.**

## Workflow

1. **Read the source md files** (report body, appendices, any separate
   findings lists). Parse out: project metadata, scope, methodology, findings,
   resolutions, contact/attribution details.
2. **Read `references/mapping.md`** and build `report.json` per its schema.
   Convert Markdown prose to HTML fragments inline (`<b>`, `<code>`,
   `<span class="mono">`, `<span class="chip …">` allowed; no headings/lists
   inside paragraphs — flatten them).
3. **Run the mandatory confirmation check** (see below) with the user before
   rendering, unless the user explicitly pre-confirmed every field.
4. Fill and render:
   ```bash
   python3 scripts/fill_template.py report.json -o report.html
   bash scripts/render.sh report.html "Project_Audit_Report.pdf"
   ```
5. **QA**: open the screenshots/rendered PDF; verify page count, TOC page
   numbers, severity counts band, chips, code-block line numbers, header-to-
   body spacing, TOC line spacing, and that no `{{…}}` placeholders remain
   (the filler warns if any do). Fix and re-run.

## Language & theme rules

- **报告默认中文**：`lang` 缺省为 `zh`，模板版式文字（封面标识、目录、页眉
  页脚、章节标题、严重度表、免责声明、联系卡）由 fill_template.py 自动替换为
  中文；`lang: "en"` 时保留英文版式。
- 封面层级：主标题 `project.name` + 副标题 `project.version`（支持 `\n`
  多行，如 "简称 GT/GOOD"）；发布状态 `report.status`（zh 默认 未公开）；
  页脚版权年份自动取自报告日期。
- 发现标题尾部的全角括号说明（如 "…（DAO 注册过渡中）"）自动拆为大标题
  下方的副标题；建议栏中文版式为「建议观点」。
- 正文语言跟随源 md；日期在中文报告中统一用 `2026-09-19`、
  `2026-09-16 – 2026-09-19` 格式。
- severity/status 标签按语言自动本地化（zh：严重/高危/中危/低危/提示 ·
  已修复/已确认/未修复），不要手工写死标签。
- **主题自由选用，无场景限制**：`theme` 取 `dark`（缺省默认）或 `light`
  均可。品牌文档第 8 节「对外报告用暗色、印刷/客户要求才用亮色」的场景
  约束已解除，也不再要求同一项目系列报告必须统一主题。两主题仍共用同一
  HTML 结构与版式几何，仅底色与天体色相不同——**不得在同页内混用两主题
  的文字色与底色，不得在亮色主题把代码块改成浅底，不得新增第三种主题
  或修改天体几何**。
- **任何内容字段不得出现「亮色版」「暗色版」字样**——主题只由 `theme`
  字段与输出文件名表达；filler 会对输出做兜底剔除。
- 主题切换按钮文案（暗色 · 海上明月 / 亮色 · 海上太阳）是品牌主题名，
  不属于「版本」标注，保持原样。

## Mandatory confirmation (do not skip)

These fields are easy to get wrong and embarrassing to ship wrong. Present them
as a compact table and get an explicit yes — especially when the source md is
ambiguous or silent:

| 字段 | 填入位置 | 必填性 |
|---|---|---|
| 署名 Prepared For（客户/项目方名称＋联系邮箱） | 封面署名栏、文档控制页 | 必填 |
| 署名 Prepared By（首席审计师姓名＋邮箱） | 封面署名栏 | 缺省自动套用固定署名 |
| 审计方联系邮箱 firm.email | 第 7 页联系卡 | 缺省自动套用固定邮箱 |
| 联系卡中栏 firm.extra（label+value，替代 Website 栏） | 第 7 页联系卡 | 可选 |
| 网站地址 firm.website | 第 7 页联系卡 | 可选，缺省整栏删除 |
| PGP 指纹 firm.pgp | 第 7 页联系卡 | 可选，缺省整行删除 |
| 捐赠钱包地址 firm.donations | 页眉打赏提示＋第 7 页捐赠行 | 可选，缺省全部删除 |
| 报告编号 / 日期 / commit / 审计周期 | 封面、页脚、文档控制页 | 必填 |

If the md names multiple auditors, put the lead in `auditor.name` and the full
list in `report.auditors`. If any 必填 field is missing from the md, ask.

**署名已固化（单一来源）**：`auditor.name` 缺省为 **Sev7ero**，`auditor.email`
与 `firm.email` 缺省同为 **Sevzero402@gmail.com**，文档控制页的 Auditors 行
亦取同一署名。四处（封面 Prepared By、文档控制页、第 7 页联系卡、页脚
署名）始终一致——满足品牌标准「署名一致性」要求。定义见
`references/author.md`，需要覆盖时在 report.json 显式给出即可。

## Optional iteration blocks（对齐 Babylon 报告版式）

以下字段**全部可选**；缺省时版式与旧版完全一致，提供后自动渲染。

| 字段 | 渲染位置 | 用途 |
|---|---|---|
| `findings[].meta` | 发现详情页元信息行 | CWE、触发可能性等 |
| `findings[].impact_table` | 发现详情页「影响分析」表 | 场景 → 影响，让影响可被证伪 |
| `findings[].evidence` | 发现详情页「证据链」 | 带标签的代码/链上证据留痕 |
| `findings[].note` | 发现详情页「说明」框 | 记录"为何不是更高危"的降级理由 |
| `uncovered` | 独立章节「未覆盖区域与残余风险」 | 披露未覆盖领域（内含可选 checklist） |

`uncovered` 出现时自动成为第 4 节，免责声明顺延为第 5 节，目录与页码由
filler 自动重算；缺省则不产生该章节，编号与页数回落。

## Hard rules

- Never fabricate findings, severities, statuses, dates, or wallet addresses.
- Severity must be one of: critical / high / medium / low / informational.
- Status must be one of: resolved / acknowledged / unresolved.
- One finding = one detail page. If a finding overflows a page, shorten the
  prose; do not shrink fonts or margins.
- Do not restyle anything. The only allowed inline markup in prose:
  `<b>`, `<code>`, `<span class="mono">`, `<span class="chip …">`.
- `resolution_html` 为空的发现会自动移除「处理状态」整块，不要留空壳。
