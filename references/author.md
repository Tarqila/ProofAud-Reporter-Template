# 署名与联系方式（单一来源）

本文件是报告署名与联系邮箱的**唯一定义处**。修改此处后，需同步更新
`scripts/fill_template.py` 顶部的常量与 `SKILL.md` 的说明。

| 项 | 值 |
|---|---|
| 署名 / Prepared By | **Sev7ero** |
| 邮箱 | **Sevzero402@gmail.com** |

## 生效位置

同一组署名与邮箱会出现在报告的四处，由 `fill_template.py` 自动注入，
保证与技能页展示完全一致（品牌标准「署名一致性」要求）：

1. 封面署名栏 Prepared By
2. 文档控制页 Auditors 行
3. 第 7 页联系卡邮箱
4. 报告全文落款口径

## 覆盖方式

某份报告需要不同署名时，在 `report.json` 中显式给出即可，缺省一律套用上表：

```json
{
  "auditor": {"name": "Sev7ero", "email": "Sevzero402@gmail.com"},
  "firm":    {"email": "Sevzero402@gmail.com"}
}
```

## 发布合规提示

- 邮箱是唯一对外联系方式，**不要在报告正文、脚本或模板里再放微信号 / 手机号**。
- 联系方式属于数据（report.json），不是注入逻辑；如需整体移除，只改本文件与脚本常量即可。
- 技能页展示的网名与邮箱必须与本文件保持一致。
