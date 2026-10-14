# proof-audit-report-builder 变更日志

## 2026-10-15 新建（从 AI_&_script 版本复制并迭代）

| 操作 | 对象 | 原因 |
|---|---|---|
| 复制 | 整包 7 个文件 → `Project&Job/Security&Audition/proof-audit-report-builder/` | 用户要求：迭代后保存到新位置，原件不动 |
| 新增 | `README.md`、`CHANGE_LOG.md`、`references/author.md` | AGENTS.md 规则 2（新项目自带文档）+ 署名单一来源 |

### 四项迭代

1. **署名固化**（`scripts/fill_template.py` + `references/author.md`）
   - 新增常量 `DEFAULT_AUTHOR_NAME = "Sev7ero"`、`DEFAULT_AUTHOR_EMAIL = "Sevzero402@gmail.com"`
   - `data["auditor"]` / `data["firm"]` 在读取后 `setdefault` 套用
   - 生效四处：封面 Prepared By、文档控制页 Auditors 行（`rep["auditors"] or [aud["name"]]`）、第 7 页联系卡（`firm.email`）、页脚口径
   - 满足品牌标准「署名一致性」：封面 / 联系卡 / 页脚署名与邮箱必须与正文一致

2. **解除主题使用限制**（`SKILL.md`）
   - 原品牌标准文档第 8 节：对外报告用暗色、印刷/客户要求才用亮色、同系列不得混用
   - 现改为：`dark`（缺省）/ `light` 均可自由选用，无场景约束
   - 保留技术性禁止项：同页不得混用两主题色、亮色主题不得改浅底代码块、不得新增第三种主题

3. **默认 Public**（`scripts/fill_template.py`）
   - `status = rep.get("status") or ("公开" if lang == "zh" else "Public")`
   - 原为 zh 默认「未公开」

4. **模板迭代**（`assets/template/index.html` + `scripts/fill_template.py`）
   - 对照 `Babylon_BugBounty/04_reports/web/Babylon_Audit_Report_EN.html` 补齐能力
   - CSS：`.evmeta` / `.evidence`+`.elabel` / `table.impact-table` / `.callout` / `ul.checklist`(+`.checked`)，含 tight/xt 紧凑档
   - `detail_cls()`：新增块计入高度估算（抽 `_w` 为函数级 + 新增 `_code_h`），自动选 常规/tight/tight.xt
   - 新增 `EXTRA_LABELS` + `finding_extra()`，在发现页 runfoot 前追加增强块
   - 新增可选章节 `uncovered`：独立成第 4 节，免责声明顺延第 5 节，目录与页码自动重算
   - **修复**：中文字典只收录 `Section 1–4`，免责声明升为第 5 节后按语言直出「第五章」/「Section 5」及页眉文案

### 验证

- 最小报告（无 auditor / 无新字段）：7 页，署名与邮箱自动出现，状态「公开」，无新增块
- 完整报告（zh，全部新字段 + 亮色）：8 页，四个增强块 + 未覆盖章节齐全，目录 1–5、页码 2–8 正确
- 完整报告（en）：8 页，Section 1–5、`Status · Public`、`Prepared by Sev7ero`，无残留 `{{}}` 占位符
- 亮色主题生成无阻（主题限制已解除）
