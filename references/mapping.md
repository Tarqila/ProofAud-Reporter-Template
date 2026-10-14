# report.json schema & Markdown conversion rules

## Schema

```json
{
  "lang": "zh | en        (可选，默认 zh：版式文字全中文；en 保留英文版式)",
  "theme": "dark | light",
  "report": {
    "id": "GT-AUD-20260919",
    "date": "2026-09-19",
    "status": "公开                (可选；缺省即公开 — zh 显示「公开」，en 显示「Public」)",
    "report_time": "2026-09-19   (可选；提供时第 2 页「审计周期」行改为「报告时间」单行日期)",
    "audit_period": "2026-09-16 – 2026-09-19",
    "commit": "a1b2c3d4e5f6789012345678901234567890abcd",
    "auditors": ["SevZero402"],
    "version_history": [{"version": "v1.0", "date": "2026-09-19", "note": "初始报告"}]
  },
  "project": {"name": "MoonVault", "version": "简称 MV\nBSC 主网 · 阶段一", "repo": "github.com/org/contracts",
              "token": "0x…                       (可选；提供时第 2 页「审计提交」行改为「Token 合约」行)"},
  "client":  {"name": "MoonVault Core Team", "email": "security@moonvault.xyz"},
  "auditor": {"name": "Alice Auditor", "email": "alice@proofaudit.io"},
  "engagement": {"type": "Full Audit", "team": "2 auditors · 2 weeks"},
  "firm": {
    "email": "hello@proofaudit.io",
    "website": "proofaudit.io",
    "extra": {"label": "黄金屋 ID", "value": "sevzero402"},
    "pgp": "0xA1B2…",
    "donations": "0x71C7…"
  },
  "scope": {
    "contracts": [{"path": "src/StakingVault.sol", "lines": "412", "commit": "a1b2c3d…",
                   "address": "0x…        (可选；提供时表格第三栏显示完整合约地址)"}],
    "tools": "Slither, Mythril",
    "fuzz_targets": "rounding and share-price invariants",
    "methodology": ["step 1 (optional; overrides default bullets)"]
  },
  "executive_summary": {
    "paragraphs": ["<p>HTML…</p>-without-tags, one string per paragraph"],
    "key_risk": "HTML, one sentence",
    "key_risk_commit": "f00ba12",
    "overall": "HTML, the overall assessment sentence(s)"
  },
  "findings": [{
    "id": "VUL-001",
    "file": "src/StakingVault.sol",
    "lines": "L212–228",
    "title": "Plain text, sentence case",
    "severity": "critical | high | medium | low | informational",
    "status": "resolved | acknowledged | unresolved",
    "description_html": "HTML fragment",
    "poc_code": "raw code string; escaped and line-numbered by the script",
    "recommendation_html": "HTML fragment",
    "resolution_html": "HTML fragment; empty/omitted → 整块移除",
    "meta": [{"label": "CWE", "value": "CWE-476"}],          (可选 → 元信息行)
    "impact_table": [{"scenario": "…", "impact": "…"}],      (可选 → 影响分析表)
    "evidence": [{"label": "E1 · …", "code": "raw code"}],   (可选 → 证据链)
    "note": "HTML fragment"                                  (可选 → 说明框)
  }],
  "appendix": ["HTML fragment per paragraph, inserted before the contact card"],
  "uncovered": {                                             (可选 → 独立第 4 节)
    "title": "未覆盖区域与残余风险 / Uncovered Areas & Residual Risk",
    "paragraphs": ["HTML fragment per paragraph"],
    "checklist": [{"text": "…", "checked": true}]
  }
}
```

- **署名缺省自动套用固定值**：`auditor.name` → `Sev7ero`；`auditor.email`
  与 `firm.email` → `Sevzero402@gmail.com`；文档控制页 Auditors 行同署名。
  定义与覆盖方式见 `references/author.md`。
- **发布状态缺省为公开**：`report.status` 缺省即「公开 / Public」，不再产出
  未公开状态；需要其他状态时显式给出。
- `firm.website` / `firm.extra` / `firm.pgp` / `firm.donations` are optional.
  `website` 与 `extra` 都缺省时整个中栏删除；`extra` 提供时替换 Website 栏
  内容（label+value）。其余字段缺失时会留下空位——必填项必须齐。
- 封面结构：h1 = `project.name`；其下副标题 = `project.version`
  （支持 `\n` 多行，如 "简称 GT/GOOD\nBSC 主网 · 阶段一"；留空则整行移除）。
  `client.name` / `engagement.team` 同样支持 `\n` 换行。
- 发现标题若以全角括号结尾（如 "持有 24% LP（名义用途为护盘）"），括号内
  部分自动拆为大标题下的副标题（.fsub，括号本身省略）；汇总表与目录仍显示完整标题。
- `poc_code` 中 ≥16 位十六进制的 0x 长串（owner()/存储槽原始输出等）自动
  中间缩写（0x000000…0000），保证代码块内不换行溢出。
- 页脚版权年份自动取 `report.date` 的年份（如 2026），无需手填。
- 封面的 commit 短哈希（前 7 位）= 审计提交（完整哈希见第 2 页）。
- `firm.donations` 提供时，自动在每页页眉生成打赏提示（.htip），并在
  第 7 页保留捐赠行；缺省则全部删除。
- `scope.methodology`, `scope.tools`, `scope.fuzz_targets`, `appendix`,
  `report.version_history`, `executive_summary.key_risk*` are optional; the
  template's sensible defaults are kept when absent.
- **禁止在任意字段（标题、编号、正文、附录、note）中出现「亮色版」
  「暗色版」字样**；主题只由 `theme` 与文件名表达（filler 兜底剔除）。

## Markdown → HTML fragment conversion

Convert inline first, then flatten block structure:

| Markdown | HTML |
|---|---|
| `**text**` / `__text__` | `<b>text</b>` |
| `` `code` `` | `<code>code</code>` |
| `` ```lang … ``` `` (inside PoC) | raw string into `poc_code` — never wrap in tags |
| paragraph | one string in `paragraphs[]` / `description_html` / … |
| heading / bullet list inside prose | flatten into sentences, or split into separate paragraphs |
| commit hash, wallet, path | `<span class="mono">…</span>` |

Do not emit `<h1–h4>`, `<ul>/<ol>`, `<table>`, `<a>` inside prose fields; the
layout owns all structure. Quote characters may stay literal; the filler
escapes plain-text fields (`name`, `email`, ids, paths, dates) automatically —
HTML fields are inserted verbatim, so escape user HTML there yourself.

## 日期格式

- 中文报告（`lang: zh`，默认）：统一 `2026-09-19`、`2026-09-16 – 2026-09-19`
  （短横线日期，勿用 "Sep 19, 2026" 这类英文格式）。
- 英文报告：`Aug 19, 2025` / `Aug 4 – Aug 15, 2025`。

## Severity & status vocabulary

severity / status 的 **chip 标签由 filler 按 lang 自动本地化**，report.json
里始终写英文枚举值，不要手写中文标签（发现详情的建议栏中文版式为「建议观点」）：

| severity | chip（zh） | chip（en） |
|---|---|---|
| critical | 严重 | Critical |
| high | 高危 | High |
| medium | 中危 | Medium |
| low | 低危 | Low |
| informational | 提示 | Info |

| status | chip（zh） | chip（en） |
|---|---|---|
| resolved | 已修复（绿框） | Resolved |
| acknowledged | 已确认（灰框） | Acknowledged |
| unresolved / open | 未修复（灰框） | Unresolved |

- The summary page counts band is recomputed from the findings list — the
  prose numbers must match it; edit the prose if they don't.
- 统计带标签（严重/高危/中危/低危/发现总数）同样自动本地化。

## Deriving fields from typical audit md

| md section | JSON field |
|---|---|
| title / project name / version | `project.name`, `project.version`（version 可留空 → 封面单行标题） |
| report id, date, audit window, commit | `report.*`（id 不带主题后缀） |
| "Audited by …" / auditor list | `auditor.*` + `report.auditors` |
| "Prepared for …" + contact | `client.*` |
| scope table (contract/lines/commit) | `scope.contracts` |
| methodology bullets | `scope.methodology` (else defaults) |
| executive summary paragraphs | `executive_summary.paragraphs` |
| per-finding sections (## VUL-001 …) | `findings[]` — map 严重程度→severity, 修复状态→status；标题尾部全角括号说明会自动拆为副标题 |
| appendices | `appendix` |

## 排版自适应（filler 自动处理，无需手调）

- 发现详情页按内容量自动选择常规 / `.tight` / `.tight.xt` 三档行距，避免与页脚重叠
  （估算含代码行折行：CJK 计双宽，每行约 88 个半角列宽）。
- 执行摘要页：正文总量 >1500 字符自动 tight，>2400 再加 xt；范围方法页方法学
  >330 字符自动 tight；附录页 >1200 字符自动 tight。
- 发现汇总表：≥10 项自动 compact 行距；>20 项自动分页（续页标题「发现汇总（续）」），
  页码与目录自动重算。
- 大标题多行行距 1.42；标题尾部括号说明自动拆为副标题（全/半角均可）。
- 除 GT 主体报告外，其余报告文件名与封面须含「附录」（en: Appendix）。
