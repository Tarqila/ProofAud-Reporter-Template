#!/usr/bin/env python3
"""Fill the Proof Audit HTML report template from a report.json file.

Usage:
    python3 fill_template.py report.json [-o report.html] [--theme dark|light]

Input: report.json — schema documented in ../references/mapping.md.
Output: a standalone HTML report (A4 print-ready, dual-theme toggle kept).
The script is deterministic: it only splices agent-authored prose into the
fixed brand/layout skeleton. It never invents content.

Language: report.json `lang` controls the brand chrome (labels, TOC, footer,
disclaimer…). Default `zh` (全中文版式); `en` keeps the original English
chrome. Severity/status chips, stats band, page numbers etc. localize with it.
"""
import argparse
import html
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "assets" / "template" / "index.html"

SEV_CLASS = {
    "critical": "crit", "high": "high", "medium": "med",
    "low": "low", "informational": "info", "info": "info",
}

# ── label vocabularies per lang ─────────────────────────────────────────────
L = {
    "en": {
        "sev": {"critical": "Critical", "high": "High", "medium": "Medium",
                "low": "Low", "informational": "Info", "info": "Info"},
        "status": {"resolved": ("tag-resolved", "Resolved"),
                   "acknowledged": ("ghost", "Acknowledged"),
                   "unresolved": ("ghost", "Unresolved"),
                   "open": ("ghost", "Unresolved")},
        "status_fallback": "Unresolved",
        "band": ["Critical", "High", "Medium", "Low", "Total Findings"],
        "key_risk": "Key Risk",
        "overall": "<b>Overall assessment:</b>",
        "toc": ["Executive Summary", "Scope & Methodology", "Findings Summary",
                "Appendix & Disclaimer"],
        "assessment": "Security Assessment",
        "page": lambda n, t: f"Page {n} of {t}",
        "tip": "BSC&nbsp;Tip&nbsp;",
    },
    "zh": {
        "sev": {"critical": "严重", "high": "高危", "medium": "中危",
                "low": "低危", "informational": "提示", "info": "提示"},
        "status": {"resolved": ("tag-resolved", "已修复"),
                   "acknowledged": ("ghost", "已确认"),
                   "unresolved": ("ghost", "未修复"),
                   "open": ("ghost", "未修复")},
        "status_fallback": "未修复",
        "band": ["严重", "高危", "中危", "低危", "发现总数"],
        "key_risk": "核心风险",
        "overall": "<b>总体评估：</b>",
        "toc": ["执行摘要", "审计范围与方法", "发现汇总", "附录与免责声明"],
        "assessment": "安全评估",
        "page": lambda n, t: f"第 {n} 页 · 共 {t} 页",
        "tip": "BSC&nbsp;打赏&nbsp;",
    },
}

# ── brand-chrome localization: en template string → zh ─────────────────────
# Applied AFTER all structural edits (which match the English template) and
# after agent content is spliced. Keys are matched longest-first.
ZH_DICT = [
    ('Proof Audit — Security Assessment Report Template', 'Proof Audit 安全评估报告'),
    ('Smart Contract Security Assessment', '智能合约安全评估'),
    ('Each finding below is presented with a description, proof of concept, recommended remediation and the\n'
     '    resolution verified during retest. Findings marked',
     '以下每项发现均包含问题描述、证据与复现、建议观点及复核确认的处理状态；标记'),
    ('<span class="chip ghost" style="font-size:7.5pt">Acknowledged</span>\n'
     '    were accepted by the project team without code change.',
     '<span class="chip ghost" style="font-size:7.5pt">已确认</span>的条目为项目方未作代码修改而接受的发现。'),
    ('This report is provided for informational purposes only and reflects the state of the audited codebase\n'
     '    at the commit identified on page 2. It does not constitute financial, legal or investment advice, nor a\n'
     '    guarantee that the reviewed contracts are free of vulnerabilities.',
     '本报告仅供信息参考，反映第 2 页所列审计提交时点被审计代码库的状态。本报告不构成财务、法律或投资建议，亦不保证被审查合约不存在漏洞。'),
    ('Security auditing is a time-bounded review process and cannot exclude the possibility of undiscovered\n'
     '    issues. Proof Audit assumes no liability for any loss arising from the use of the audited software.\n'
     '    Contracts deployed after the audit commit are outside the scope of this report.',
     '安全审计是有时间边界的审查过程，无法排除未发现问题的可能性。Proof Audit 对因使用被审计软件而产生的任何损失不承担法律责任。审计提交之后部署的合约不在本报告范围之内。'),
    ('Direct loss of funds, or broken contract invariants with no viable mitigation.',
     '直接导致资金损失，或合约不变量被破坏且无有效缓解措施。'),
    ('Likely loss of funds under realistic conditions, or severe degradation of core functionality.',
     '在现实条件下可能导致资金损失，或核心功能严重受损。'),
    ('Limited impact requiring specific conditions, or deviations from best practice with security relevance.',
     '需在特定条件下才产生有限影响，或偏离最佳实践且具有安全相关性。'),
    ('Minor issue; minimal direct impact, fix recommended.', '次要问题，直接影响有限，建议修复。'),
    ('No security impact; observations and hardening suggestions.', '无安全影响；观察记录与加固建议。'),
    ('Adversarial review of privileged roles, upgrade paths and external call surfaces',
     '对特权角色、升级路径与外部调用面进行对抗性审查'),
    ('Verification of fixes in a dedicated retest phase', '在专项复测阶段验证修复情况'),
    ('Manual line-by-line review of all in-scope source code', '对全部范围内源代码进行逐行人工审查'),
    ('<th style="width:70px">ID</th><th>Title</th><th style="width:100px">Severity</th><th style="width:110px">Status</th>',
     '<th style="width:70px">编号</th><th>标题</th><th style="width:100px">严重度</th><th style="width:110px">状态</th>'),
    ('<th>Contract</th><th style="width:64px">Lines</th><th>Address</th>',
     '<th>合约</th><th style="width:64px">行数</th><th>合约地址</th>'),
    ('2.1 &nbsp;In-Scope Contracts', '2.1 &nbsp;审计范围内的合约'),
    ('2.2 &nbsp;Methodology', '2.2 &nbsp;审计方法'),
    ('2.3 &nbsp;Severity Classification', '2.3 &nbsp;严重程度分级'),
    (' — Security Assessment</span>', ' — 安全评估</span>'),
    ('1 · Executive Summary', '1 · 执行摘要'),
    ('2 · Scope &amp; Methodology', '2 · 审计范围与方法'),
    ('3 · Findings Summary', '3 · 发现汇总'),
    ('4 · Appendix &amp; Disclaimer', '4 · 附录与免责声明'),
    ('<span class="t">Executive Summary</span>', '<span class="t">执行摘要</span>'),
    ('<span class="t">Scope &amp; Methodology</span>', '<span class="t">审计范围与方法</span>'),
    ('<span class="t">Findings Summary</span>', '<span class="t">发现汇总</span>'),
    ('<span class="t">Appendix &amp; Disclaimer</span>', '<span class="t">附录与免责声明</span>'),
    ('>Executive Summary</h2>', '>执行摘要</h2>'),
    ('>Scope &amp; Methodology</h2>', '>审计范围与方法</h2>'),
    ('>Findings Summary</h2>', '>发现汇总</h2>'),
    ('>Disclaimer</h2>', '>免责声明</h2>'),
    ('>Document Control</div>', '>文档控制</div>'),
    ('>Report Information</h2>', '>报告信息</h2>'),
    ('>Version History</td>', '>版本历史</td>'),
    ('>Commit Audited</td>', '>审计提交</td>'),
    ('>Token Contract</td>', '>Token 合约</td>'),
    ('>Audit Period</td>', '>审计周期</td>'),
    ('>Report Time</td>', '>报告时间</td>'),
    ('>Auditors</td>', '>审计人员</td>'),
    ('>Report ID</td>', '>报告编号</td>'),
    ('>Project</td>', '>项目名称</td>'),
    ('>Contents</div>', '>目录</div>'),
    ('<div class="lbl">Total Findings</div>', '<div class="lbl">发现总数</div>'),
    ('<div class="lbl">Critical</div>', '<div class="lbl">严重</div>'),
    ('<div class="lbl">Medium</div>', '<div class="lbl">中危</div>'),
    ('<div class="lbl">High</div>', '<div class="lbl">高危</div>'),
    ('<div class="lbl">Low</div>', '<div class="lbl">低危</div>'),
    ('<span class="ct">Key Risk</span>', '<span class="ct">核心风险</span>'),
    ('>Description</div>', '>问题描述</div>'),
    ('>Proof of Concept</div>', '>证据与复现</div>'),
    ('>Recommendation</div>', '>建议观点</div>'),
    ('>Resolution</div>', '>处理状态</div>'),
    ('>Smart Contract Security</div>', '>智能合约安全</div>'),
    ('Donations · Optional', '打赏 · 自愿'),
    ('<span class="ct">Key Risk</span>', '<span class="ct">核心风险</span>'),
    ('Issued ', '发布日期 '),
    ('End of Report', '报告完'),
    ('Status · ', '状态 · '),
    ('Engagement type', '审计类型'),
    ('Prepared for', '报告对象'),
    ('Prepared by', '编制'),
    ('Report <b>#', '报告 <b>#'),
    ('Audited by <b>', '审计方 <b>'),
    ('Security Assessment<br>', '安全评估<br>'),
    ('>Website</div>', '>网站</div>'),
    ('>Report</div>', '>报告</div>'),
    ('Section 1', '第一章'), ('Section 2', '第二章'),
    ('Section 3', '第三章'), ('Section 4', '第四章'),
    ('>Critical</span>', '>严重</span>'),
    ('>High</span>', '>高危</span>'),
    ('>Medium</span>', '>中危</span>'),
    ('>Low</span>', '>低危</span>'),
    ('>Informational</span>', '>提示</span>'),
    ('>Resolved</span>', '>已修复</span>'),
    ('>Acknowledged</span>', '>已确认</span>'),
    ('<div class="lbl">High</div>', '<div class="lbl">高危</div>'),
    ('<div class="lbl">Low</div>', '<div class="lbl">低危</div>'),
]
ZH_DICT.sort(key=lambda kv: len(kv[0]), reverse=True)

BANNED_WORDS = ("亮色版", "暗色版")

# 固定署名：报告封面 / 联系卡 / 页脚的唯一来源，须与技能页展示完全一致
DEFAULT_AUTHOR_NAME = "Sev7ero"
DEFAULT_AUTHOR_EMAIL = "Sevzero402@gmail.com"


def esc(x):
    return html.escape(str(x), quote=False)


def paragraphs(items, cls="body"):
    """Wrap a list of HTML paragraph strings."""
    return "\n".join(f'  <p class="{cls}">{p}</p>' for p in items)


def poc_block(code):
    """Render numbered code lines like the template's <pre class=\"codeblock\">.

    Long 0x-hex strings (≥16 hex chars, e.g. raw owner()/slot outputs) are
    middle-truncated so no line ever exceeds the code-block width.
    """
    def shorten(m):
        h = m.group(0)
        return h[:8] + "…" + h[-4:]
    lines = code.rstrip("\n").split("\n")
    out = []
    for i, ln in enumerate(lines, 1):
        ln = re.sub(r"0x[0-9a-fA-F]{16,}", shorten, ln)
        out.append(f'<span class="ln">{i}</span>  {esc(ln)}')
    return '<pre class="codeblock">' + "\n".join(out) + "</pre>"



def _plain_len(html_frag):
    return len(re.sub(r"<[^>]+>", "", html_frag or ""))


EXTRA_LABELS = {
    "zh": {"impact": "影响分析", "scenario": "场景", "impact_col": "影响",
           "evidence": "证据链", "note": "说明"},
    "en": {"impact": "Impact Assessment", "scenario": "Scenario",
           "impact_col": "Impact", "evidence": "Evidence Chain", "note": "Note"},
}


def finding_extra(f, lang):
    """发现详情页的可选增强块：影响分析表 / 证据链 / 说明框 / 元信息行。

    对应 report.json 的可选字段 impact_table / evidence / note / meta；
    全部缺席时返回空串，版式与旧版完全一致。
    """
    t = EXTRA_LABELS[lang]
    out = ""

    rows = f.get("impact_table") or []
    if rows:
        body = "".join(
            f'<tr><td>{esc(r.get("scenario", ""))}</td><td>{r.get("impact", "")}</td></tr>'
            for r in rows)
        out += ('  <div class="fblock">\n'
                f'    <div class="fh">{t["impact"]}</div>\n'
                f'    <table class="impact-table">'
                f'<tr><th>{t["scenario"]}</th><th>{t["impact_col"]}</th></tr>'
                f'{body}</table>\n  </div>\n\n')

    evs = f.get("evidence") or []
    if evs:
        blocks = "".join(
            f'    <div class="evidence"><span class="elabel">{esc(e.get("label", ""))}</span>'
            f'{poc_block(e.get("code", "") or "")}</div>\n'
            for e in evs)
        out += ('  <div class="fblock">\n'
                f'    <div class="fh">{t["evidence"]}</div>\n'
                f'    <div class="fb">\n{blocks}    </div>\n  </div>\n\n')

    if f.get("note", "").strip():
        out += ('  <div class="fblock">\n'
                f'    <div class="fh">{t["note"]}</div>\n'
                f'    <div class="fb"><div class="callout">{f["note"]}</div></div>\n'
                '  </div>\n\n')

    meta = f.get("meta") or []
    if meta:
        items = "".join(
            f'<span class="item">{esc(m.get("label", ""))} <b>{esc(m.get("value", ""))}</b></span>'
            for m in meta)
        out += f'  <div class="evmeta">{items}</div>\n\n'

    return out


def detail_cls(f, lang):
    """Pick the section class for a finding detail page from a height estimate
    (usable A4 content height ≈ 941 px at 96 dpi)."""
    cpl = 44 if lang == "zh" else 78

    def _w(ln):  # code lines wrap: CJK chars count double, ~88 ascii columns
        return sum(2 if ord(ch) > 0x2E80 else 1 for ch in ln)

    def _code_h(code):
        code = (code or "").rstrip()
        if not code.strip():
            return 0
        n_lines = sum(max(1, -(-_w(ln) // 88)) for ln in code.split("\n"))
        return 32 + n_lines * 16.7 + 12 + 28

    h = 200  # finding head + running clearance
    h += 32 + max(1, -(-_plain_len(f.get("description_html", "")) // cpl)) * 19.5 + 28
    h += _code_h(f.get("poc_code", ""))
    for key in ("recommendation_html", "resolution_html"):
        txt = f.get(key, "")
        if txt.strip():
            h += 32 + max(1, -(-_plain_len(txt) // cpl)) * 19.5 + 28
    # optional iteration blocks: impact table / evidence chain / note
    if f.get("impact_table"):
        h += 32 + len(f["impact_table"]) * 26 + 20
    for e in f.get("evidence") or []:
        h += 32 + _code_h(e.get("code", "")) + 18
    if (f.get("note") or "").strip():
        h += 32 + max(1, -(-_plain_len(f["note"]) // cpl)) * 19.5 + 28
    if f.get("meta"):
        h += 26
    if h > 1120:
        return "page tight xt"
    if h > 941:
        return "page tight"
    return "page"


def fail(msg):
    sys.exit(f"[fill_template] ERROR: {msg}")


def sanitize(text):
    """Strip banned theme words from any text that will land in the report."""
    for w in BANNED_WORDS:
        text = text.replace(w, "")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path")
    ap.add_argument("-o", "--output", default="report.html")
    ap.add_argument("--theme", choices=["dark", "light"], default=None)
    a = ap.parse_args()

    data = json.load(open(a.json_path, encoding="utf-8"))
    tpl = open(TEMPLATE, encoding="utf-8").read()

    lang = data.get("lang", "zh")
    if lang not in L:
        fail(f'lang must be one of {sorted(L)}')
    lab = L[lang]

    theme = a.theme or data.get("theme", "dark")
    if theme not in ("dark", "light"):
        fail('theme must be "dark" or "light"')
    tpl = tpl.replace('data-theme="dark"', f'data-theme="{theme}"', 1)
    tpl = tpl.replace('id="themeLabel">暗色 · 海上明月',
                      f'id="themeLabel">{"暗色 · 海上明月" if theme == "dark" else "亮色 · 海上太阳"}')
    tpl = tpl.replace('<html lang="en"', f'<html lang="{"zh-CN" if lang == "zh" else "en"}"', 1)

    # ── flat fields (exact placeholder strings from the template) ──────────
    rep = data.get("report", {})
    prj = data.get("project", {})
    cli = data.get("client", {})
    aud = data.get("auditor", {})
    eng = data.get("engagement", {})
    firm = data.get("firm", {})
    # report.json 未指定时套用固定署名，保证每份报告都能追溯到同一作者与邮箱
    aud.setdefault("name", DEFAULT_AUTHOR_NAME)
    aud.setdefault("email", DEFAULT_AUTHOR_EMAIL)
    firm.setdefault("email", DEFAULT_AUTHOR_EMAIL)

    # empty project.version → drop the cover subtitle line entirely
    if not prj.get("version"):
        tpl = tpl.replace('    <div class="vers">{{Protocol v2.0}}</div>\n', "", 1)

    # report.commit empty (e.g. evidence appendix) → drop the cover commit
    # segment and the whole Commit Audited row
    if not rep.get("commit"):
        tpl = tpl.replace(' &nbsp;·&nbsp; Commit <span class="mono" style="color:var(--cover-ink)">{{a1b2c3d}}</span>', "", 1)
        tpl = tpl.replace(
            '      <tr><td class="k">Commit Audited</td>'
            '<td class="v mono">{{a1b2c3d4e5f6789012345678901234567890abcd}}</td></tr>\n', "", 1)

    # project.token → page-2 "Commit Audited" row becomes the token contract row
    if prj.get("token"):
        tpl = tpl.replace(
            '<tr><td class="k">Commit Audited</td>'
            '<td class="v mono">{{a1b2c3d4e5f6789012345678901234567890abcd}}</td></tr>',
            f'<tr><td class="k">Token Contract</td><td class="v mono">{esc(prj["token"])}</td></tr>', 1)

    # report.report_time → page-2 "Audit Period" row becomes a single-date 报告时间 row
    if rep.get("report_time"):
        tpl = tpl.replace(
            '<tr><td class="k">Audit Period</td><td class="v">{{Aug 4 – Aug 15, 2025}}</td></tr>',
            f'<tr><td class="k">Report Time</td><td class="v">{esc(rep["report_time"])}</td></tr>', 1)

    # remove the sample version-history line before placeholders are flattened
    tpl = tpl.replace(
        "v1.0 {{Aug 15, 2025}} — initial report<br>v1.1 {{Aug 19, 2025}} — retest findings, final", "")

    # publication status on the cover — 所有报告默认对外公开（不再区分 未公开）
    status = rep.get("status") or ("公开" if lang == "zh" else "Public")

    flat = {
        "{{PA-2025-001}}": rep.get("id", ""),
        "{{Aug 19, 2025}}": rep.get("date", ""),
        "{{August 19, 2025}}": rep.get("date", ""),
        "{{Aug 4 – Aug 15, 2025}}": rep.get("audit_period", ""),
        "{{a1b2c3d}}": (rep.get("commit") or "")[:7],
        "{{a1b2c3d4e5f6789012345678901234567890abcd}}": rep.get("commit", ""),
        "{{Project Name}}": sanitize(prj.get("name", "")),
        "{{Protocol v2.0}}": sanitize(prj.get("version", "")),
        "{{repository-url}}": prj.get("repo", ""),
        "{{Client / Project Team}}": sanitize(cli.get("name", "")),
        "{{contact@project.xyz}}": cli.get("email", ""),
        "{{Lead Auditor}}": aud.get("name", ""),
        "{{auditor@proofaudit.io}}": aud.get("email", ""),
        "{{Full Audit / Diff Audit}}": sanitize(eng.get("type", "")),
        "{{2 auditors · 2 weeks}}": sanitize(eng.get("team", "")),
        "{{0xA1B2…}}": firm.get("pgp", ""),
        "{{0x71C7656EC7ab88b098defB751B7401B5f6d8976F}}": firm.get("donations", ""),
        "{{Public}}": status,
    }
    for k, v in flat.items():
        tpl = tpl.replace(k, esc(v).replace("\n", "<br>"))

    # default methodology bullets carry inline placeholders; fill or de-brace them
    scope_pre = data.get("scope", {})
    tools = scope_pre.get("tools", "Slither, Mythril")
    fuzz = scope_pre.get("fuzz_targets", "rounding and share-price invariants")
    if lang == "zh":
        tpl = tpl.replace("<li>Static analysis with {{Slither, Mythril}}</li>",
                          f"<li>使用 {esc(tools)} 进行静态分析</li>")
        tpl = tpl.replace("<li>Property-based fuzzing of {{rounding and share-price invariants}}</li>",
                          f"<li>针对 {esc(fuzz)} 进行基于属性的模糊测试</li>")
    else:
        tpl = tpl.replace("{{Slither, Mythril}}", esc(tools))
        tpl = tpl.replace("{{rounding and share-price invariants}}", esc(fuzz))

    # firm email on the contact card (non-placeholder sample value)
    if firm.get("email"):
        tpl = tpl.replace("hello@proofaudit.io", esc(firm["email"]))
    else:
        # no contact line available → drop the sample mono line rather than
        # leaving a wrong default address on the card
        tpl = tpl.replace('      <div class="mono">hello@proofaudit.io</div>\n', "", 1)

    # ── optional blocks: website/extra column / pgp line / donation line ───
    extra = firm.get("extra")  # optional {"label":…, "value":…} middle column
    if extra:
        tpl = re.sub(
            r'<div class="k">Website</div>\s*<div class="v">proofaudit\.io</div>',
            f'<div class="k">{esc(extra.get("label", ""))}</div>'
            f'<div class="v">{esc(extra.get("value", ""))}</div>',
            tpl, count=1)
    elif firm.get("website"):
        tpl = tpl.replace('<div class="v">proofaudit.io</div>',
                          f'<div class="v">{esc(firm["website"])}</div>')
    else:
        tpl = re.sub(
            r'\s*<div class="c">\s*<div class="k">Website</div>.*?</div>\s*</div>',
            "", tpl, count=1, flags=re.S)
    if not firm.get("pgp"):
        tpl = re.sub(r'\s*<div class="mono">PGP [^<]*</div>', "", tpl, count=1)
    if not firm.get("donations"):
        # drop the whole donate line (it sits right before the endmark)
        tpl = re.sub(r'\s*<div class="donate">.*?<div class="endmark">',
                     '\n\n  <div class="endmark">', tpl, count=1, flags=re.S)

    # ── document control: auditors + version history ───────────────────────
    auditors = rep.get("auditors") or [aud.get("name", "")]
    tpl = tpl.replace("{{Auditor One}}, {{Auditor Two}}", esc(", ".join(auditors)))
    vh = rep.get("version_history") or []
    if vh:
        rows = "<br>".join(
            f'{esc(v.get("version", ""))} {esc(v.get("date", ""))}'
            + (f' — {esc(v.get("note", ""))}' if v.get("note") else "")
            for v in vh)
        tpl = re.sub(
            r'<td class="k">Version History</td><td class="v">.*?</td></tr>',
            f'<td class="k">Version History</td><td class="v">{rows}</td></tr>',
            tpl, count=1, flags=re.S)
    else:
        # no version history → drop the whole row, not an empty shell
        tpl = re.sub(r'\s*<tr><td class="k">Version History</td><td class="v">.*?</td></tr>',
                     "", tpl, count=1, flags=re.S)

    # ── executive summary page ─────────────────────────────────────────────
    ex = data.get("executive_summary", {})
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    findings = data.get("findings", [])
    for f in findings:
        sev = str(f.get("severity", "")).lower()
        if sev in counts:
            counts[sev] += 1
    total = len(findings)

    band = "\n".join([
        '  <div class="exstats">',
        f'    <div class="cell"><div class="num" style="color:var(--crit)">{counts["critical"]}</div><div class="lbl">{lab["band"][0]}</div></div>',
        f'    <div class="cell"><div class="num" style="color:var(--high)">{counts["high"]}</div><div class="lbl">{lab["band"][1]}</div></div>',
        f'    <div class="cell"><div class="num" style="color:var(--med)">{counts["medium"]}</div><div class="lbl">{lab["band"][2]}</div></div>',
        f'    <div class="cell"><div class="num" style="color:var(--low)">{counts["low"]}</div><div class="lbl">{lab["band"][3]}</div></div>',
        f'    <div class="cell"><div class="num">{total}</div><div class="lbl">{lab["band"][4]}</div></div>',
        '  </div>',
    ])
    callout = ""
    if ex.get("key_risk"):
        kc = ""
        if ex.get("key_risk_commit"):
            kc = (f' 已在提交 <span class="mono">{esc(ex["key_risk_commit"])}</span> 中修复。'
                  if lang == "zh" else
                  f' This was addressed in commit <span class="mono">{esc(ex["key_risk_commit"])}</span>.')
        callout = (f'  <div class="callout">\n    <span class="ct">{lab["key_risk"]}</span>\n'
                   f'    {ex["key_risk"]}{kc}\n  </div>\n')
    body = paragraphs(ex.get("paragraphs", []))
    if ex.get("overall"):
        body += f'\n  <p class="body">\n    {lab["overall"]} {ex["overall"]}\n  </p>'

    m = re.search(
        r'(<h2 class="section-title">Executive Summary</h2>)\n.*?(?=\n  <div class="runfoot">)',
        tpl, flags=re.S)
    if not m:
        fail("Executive Summary section not found in template")
    tpl = tpl[:m.start()] + m.group(1) + "\n\n" + body + "\n\n" + band + "\n\n" + callout.rstrip("\n") + tpl[m.end():]

    # long prose (typical for English) risks overflowing the fixed A4 page →
    # switch that page to the compact .tight metrics
    ex_total = sum(len(p) for p in ex.get("paragraphs", [])) + len(ex.get("overall", "")) + len(ex.get("key_risk", ""))
    if ex_total > 1500:
        cls = "page tight xt" if ex_total > 2400 else "page tight"
        tpl = tpl.replace('<!-- ═══════════ PAGE 3 · EXECUTIVE SUMMARY ═══════════ -->\n<section class="page">',
                          f'<!-- ═══════════ PAGE 3 · EXECUTIVE SUMMARY ═══════════ -->\n<section class="{cls}">', 1)

    # ── scope page ─────────────────────────────────────────────────────────
    scope = data.get("scope", {})
    contracts = scope.get("contracts", [])
    if contracts:
        rows = "".join(
            f'    <tr><td class="mono">{esc(c.get("path", ""))}</td>'
            f'<td class="mono">{esc(c.get("lines", ""))}</td>'
            f'<td class="mono">{esc(c.get("address") or c.get("commit", "")[:7])}</td></tr>\n'
            for c in contracts)
        tpl = re.sub(
            r'(<table class="scope-table">\n    <tr><th>Contract</th><th style="width:64px">Lines</th><th>Address</th></tr>\n).*?(  </table>)',
            r"\1" + rows + r"\2", tpl, count=1, flags=re.S)
    steps = scope.get("methodology")
    if steps:
        items = "\n".join(f"    <li>{s}</li>" for s in steps)
        tpl = re.sub(r'(<ul class="method">)\n.*?(  </ul>)',
                     r"\1\n" + items + "\n" + r"\2", tpl, count=1, flags=re.S)
        if sum(len(x) for x in steps) > 330:  # EN methodology runs long → compact page 4
            tpl = tpl.replace('<!-- ═══════════ PAGE 4 · SCOPE & METHODOLOGY ═══════════ -->\n<section class="page">',
                              '<!-- ═══════════ PAGE 4 · SCOPE & METHODOLOGY ═══════════ -->\n<section class="page tight">', 1)

    # ── findings summary table (compact ≥10 findings; paginate >22) ────────
    extra_summary_pages = 0
    if findings:
        rows = []
        for f in findings:
            sev = str(f.get("severity", "")).lower()
            st = str(f.get("status", "")).lower()
            cls, label = lab["status"].get(st, ("ghost", lab["status_fallback"]))
            rows.append(
                f'    <tr>\n'
                f'      <td class="id">{esc(f.get("id", ""))}</td>\n'
                f'      <td class="tt">{f["title"]}</td>\n'
                f'      <td><span class="chip {SEV_CLASS.get(sev, "info")}">{lab["sev"].get(sev, lab["sev"]["info"])}</span></td>\n'
                f'      <td><span class="chip {cls}">{label}</span></td>\n'
                f'    </tr>')
        n_rows = len(rows)
        table_cls = "findings compact" if n_rows >= 10 else "findings"
        chunks = [rows[i:i + 20] for i in range(0, n_rows, 20)] if n_rows > 20 else [rows]
        extra_summary_pages = len(chunks) - 1
        first_rows = "\n".join(chunks[0]) + "\n"

        def _tbl(m):
            return (m.group(1) + (" compact" if n_rows >= 10 else "") + m.group(2)
                    + first_rows + m.group(3))
        tpl = re.sub(
            r'(<table class="findings)(">\n    <tr><th[^>]*>ID</th><th>Title</th>.*?</tr>\n).*?(  </table>)',
            _tbl, tpl, count=1, flags=re.S)

        if extra_summary_pages:
            # the note paragraph no longer fits once the table paginates
            tpl = re.sub(r'\s*<p class="body" style="margin-top:34px">\s*Each finding below.*?</p>',
                         "", tpl, count=1, flags=re.S)
            cont_suffix = "（续）" if lang == "zh" else " · Continued"
            cont_pages = ""
            for chunk in chunks[1:]:
                cont_rows = "\n".join(chunk)
                cont_pages += (
                    '\n\n<!-- ═══════════ PAGE 5 · FINDINGS SUMMARY (CONTINUED) ═══════════ -->\n'
                    '<section class="page">\n'
                    '  <div class="runhead"><span class="brand"><svg style="width:11px;height:11px;vertical-align:-1px;margin-right:7px" viewBox="0 0 26 26" fill="none"><path d="M13 1 L24 6 V13 C24 19.5 19.5 24 13 25.5 C6.5 24 2 19.5 2 13 V6 Z" stroke="currentColor" stroke-width="2.2" fill="none"/><path d="M8.5 12.6 L11.8 15.9 L17.8 9.6" stroke="var(--accent)" stroke-width="2.8" fill="none"/></svg>Proof <em>Audit</em></span>'
                    f'<span>3 · {lab["toc"][2]}{cont_suffix}</span><!--HTIP--></div>\n\n'
                    f'  <div class="cont-head">{lab["toc"][2]}{cont_suffix}</div>\n'
                    f'  <table class="findings compact">\n'
                    f'    <tr><th style="width:70px">ID</th><th>Title</th><th style="width:100px">Severity</th><th style="width:110px">Status</th></tr>\n'
                    f'{cont_rows}\n  </table>\n\n'
                    '  <div class="runfoot">\n    <span>© 2025 Proof Audit</span>\n'
                    '    <span class="mono">' + esc(rep.get("id", "")) + '</span>\n'
                    '    <span>Page 5 of 7</span>\n  </div>\n'
                    '</section>')
            tpl = re.sub(r'(?=<!-- ═+ PAGE 6 · FINDING DETAIL)',
                         lambda m: cont_pages + '\n\n', tpl, count=1)

    # ── finding detail pages (one per finding) ─────────────────────────────
    m = re.search(
        r'(<!-- ═+ PAGE 6 · FINDING DETAIL.*?-->\n<section class="page">).*?(?=<!-- ═+ PAGE 7 ·)',
        tpl, flags=re.S)
    if not m:
        fail("Finding detail template block not found")
    det_tpl = tpl[m.start():m.end()]

    pages = ""
    for i, f in enumerate(findings, 1):
        sev = str(f.get("severity", "")).lower()
        st = str(f.get("status", "")).lower()
        scls, slabel = lab["status"].get(st, ("ghost", lab["status_fallback"]))
        fid = " · ".join(p for p in (f.get("id", ""), f.get("file", ""), f.get("lines", "")) if p)
        # trailing parenthetical (full- or half-width) → subtitle under the big
        # title (the brackets themselves are dropped — the subtitle style replaces them)
        mt = re.match(r"^(.*?)[（\(]([^（）()]+)[）\)]\s*$", f.get("title", ""))
        if mt:
            title_main = mt.group(1).rstrip()
            title_sub = mt.group(2)
            h3_html = (f'<h3>{title_main}</h3>\n'
                       f'      <div class="fsub">{title_sub}</div>')
        else:
            h3_html = f'<h3>{f["title"]}</h3>'
        page = det_tpl
        page = page.replace("3.1 · VUL-001", f"3.{i} · {esc(f.get('id', ''))}")
        page = re.sub(
            r'<div class="fid">.*?</div>\s*<h3>.*?</h3>',
            f'<div class="fid">{esc(fid)}</div>\n      {h3_html}',
            page, count=1, flags=re.S)
        page = re.sub(
            r'<span class="chip crit">Critical</span>\s*'
            r'<span class="chip tag-resolved">Resolved</span>',
            f'<span class="chip {SEV_CLASS.get(sev, "info")}">{lab["sev"].get(sev, lab["sev"]["info"])}</span>\n'
            f'      <span class="chip {scls}">{slabel}</span>',
            page, count=1)
        page = re.sub(r'(<div class="fh">Description</div>\s*<div class="fb">).*?(</div>)',
                      r"\1\n      " + f["description_html"] + r"\n    \2", page, count=1, flags=re.S)
        page = re.sub(r'(<div class="fh">Proof of Concept</div>\s*)<pre class="codeblock">.*?</pre>',
                      r"\1" + poc_block(f.get("poc_code", "")), page, count=1, flags=re.S)
        page = re.sub(r'(<div class="fh">Recommendation</div>\s*<div class="fb">).*?(</div>)',
                      r"\1\n      " + f["recommendation_html"] + r"\n    \2", page, count=1, flags=re.S)
        # empty resolution → drop the whole block instead of an empty shell
        if f.get("resolution_html", "").strip():
            page = re.sub(r'(<div class="fh">Resolution</div>\s*<div class="fb">).*?(</div>\s*</div>)',
                          r"\1\n      " + f["resolution_html"] + r"\n    \2", page, count=1, flags=re.S)
        else:
            page = re.sub(r'\s*<div class="fblock">\s*<div class="fh">Resolution</div>\s*<div class="fb">.*?</div>\s*</div>',
                          "", page, count=1, flags=re.S)
        # optional iteration blocks appended before the running foot
        extra = finding_extra(f, lang)
        if extra:
            page = page.replace('<div class="runfoot">',
                                extra + '  <div class="runfoot">', 1)
        cls = detail_cls(f, lang)
        if cls != "page":
            page = page.replace('<section class="page">', f'<section class="{cls}">', 1)
        pages += page + "\n\n"
    tpl = tpl[:m.start()] + pages.rstrip("\n") + tpl[m.end():]

    # ── 未覆盖区域与残余风险（可选独立章节，对齐 Babylon 报告版式） ──────────
    unc = data.get("uncovered") or {}
    unc_title, unc_pages = "", 0
    if unc.get("paragraphs") or unc.get("checklist"):
        unc_title = unc.get("title") or {
            "zh": "未覆盖区域与残余风险",
            "en": "Uncovered Areas & Residual Risk"}[lang]
        body = paragraphs(unc.get("paragraphs") or [])
        items = unc.get("checklist") or []
        cl = ""
        if items:
            lis = "".join(
                f'<li class="checked">{i.get("text", "")}</li>' if i.get("checked")
                else f'<li>{i.get("text", "")}</li>' for i in items)
            cl = f'  <ul class="checklist">{lis}</ul>\n\n'
        _rh = re.search(r'<div class="runhead">.*?--></div>', tpl, re.S).group(0)
        runhead = re.sub(r'<span>[^<]*</span><!--HTIP-->',
                         f'<span>{esc(unc_title)}</span><!--HTIP-->', _rh, count=1)
        unc_page = (
            '<!-- ═══════════ PAGE · UNCOVERED AREAS & RESIDUAL RISK ═══════════ -->\n'
            '<section class="page">\n'
            f'  {runhead}\n\n'
            '  <div class="section-num">Section 4</div>\n'
            f'  <h2 class="section-title">{esc(unc_title)}</h2>\n\n'
            f'{body}\n\n{cl}'
            '  <div class="runfoot">\n'
            '    <span>© 2025 Proof Audit</span>\n'
            f'    <span class="mono">{esc(rep.get("id", ""))}</span>\n'
            '    <span>Page 7 of 7</span>\n'
            '  </div>\n'
            '</section>\n\n')
        tpl = tpl.replace('<!-- ═══════════ PAGE 7 · DISCLAIMER & CONTACT ═══════════ -->',
                          unc_page + '<!-- ═══════════ PAGE 7 · DISCLAIMER &amp; CONTACT ═══════════ -->', 1)
        # 免责声明顺延为第 5 节（中文字典只收录 Section 1–4，故按语言直出）
        sec5 = "第五章" if lang == "zh" else "Section 5"
        appx5 = "5 · 附录与免责声明" if lang == "zh" else "5 · Appendix &amp; Disclaimer"
        tpl = tpl.replace(
            '<div class="section-num">Section 4</div>\n  <h2 class="section-title">Disclaimer</h2>',
            f'<div class="section-num">{sec5}</div>\n  <h2 class="section-title">Disclaimer</h2>', 1)
        tpl = tpl.replace('<span>4 · Appendix &amp; Disclaimer</span>',
                          f'<span>{appx5}</span>', 1)
        unc_pages = 1

    # ── TOC rebuild ────────────────────────────────────────────────────────
    n = len(findings)
    disc_page = 6 + n + extra_summary_pages + unc_pages
    t = lab["toc"]
    # page 2 space budget: per-finding subrows fit only when n ≤ 9; beyond
    # that the TOC lists sections only (findings remain reachable via p.5)
    show_subrows = n <= 9
    compact = ' class="compact"' if show_subrows and n > 6 else ""
    subrows = "".join(
        f'    <div class="row sub"><span class="n">3.{i}</span>'
        f'<span class="t">{esc(f.get("id", ""))} · {f["title"]}</span>'
        f'<span class="dots"></span><span class="p">{5 + i}</span></div>\n'
        for i, f in enumerate(findings, 1)) if show_subrows else ""
    unc_row, last_no = "", 4
    if unc_pages:
        unc_row = (f'    <div class="row"><span class="n">4</span>'
                   f'<span class="t">{esc(unc_title)}</span><span class="dots"></span>'
                   f'<span class="p">{disc_page - 1}</span></div>\n')
        last_no = 5
    toc = (
        f'    <div class="row"><span class="n">1</span><span class="t">{t[0]}</span><span class="dots"></span><span class="p">3</span></div>\n'
        f'    <div class="row"><span class="n">2</span><span class="t">{t[1]}</span><span class="dots"></span><span class="p">4</span></div>\n'
        f'    <div class="row"><span class="n">3</span><span class="t">{t[2]}</span><span class="dots"></span><span class="p">5</span></div>\n'
        + subrows + unc_row +
        f'    <div class="row"><span class="n">{last_no}</span><span class="t">{t[3]}</span><span class="dots"></span><span class="p">{disc_page}</span></div>')
    tpl = re.sub(r'(<div class="toc")[^>]*>.*?(  </div>\n\n  <div class="runfoot">)',
                 r"\1" + compact + ">\n" + toc + r"\n\2", tpl, count=1, flags=re.S)

    # ── appendix paragraphs (inserted before the contact card) ─────────────
    apx = data.get("appendix") or []
    if apx:
        tpl = tpl.replace('<div class="contact">',
                          paragraphs(apx) + '\n\n  <div class="contact">', 1)
        if sum(len(a) for a in apx) > 1200:
            tpl = tpl.replace('<!-- ═══════════ PAGE 7 · DISCLAIMER & CONTACT ═══════════ -->\n<section class="page disclaimer">',
                              '<!-- ═══════════ PAGE 7 · DISCLAIMER & CONTACT ═══════════ -->\n<section class="page disclaimer tight">', 1)

    # ── running-header tip (optional, from donations address) ──────────────
    if firm.get("donations"):
        tip = (f'<span class="htip">{lab["tip"]}<span class="mono">{esc(firm["donations"])}</span></span>')
        tpl = tpl.replace("<!--HTIP-->", tip)
    else:
        tpl = tpl.replace("<!--HTIP-->", "")

    # ── brand-chrome localization (after all English-pattern structure edits) ──
    if lang == "zh":
        for en, zh in ZH_DICT:
            tpl = tpl.replace(en, zh)

    # ── page numbers: cover is unnumbered; numbering starts at page 2 ──────
    n_runfeet = len(re.findall(r'<div class="runfoot">', tpl))
    total_pages = n_runfeet + 1
    counter = iter(range(2, total_pages + 1))

    def repl(mo):
        return lab["page"](next(counter), total_pages)

    tpl = re.sub(r"Page \d+ of \d+", repl, tpl)

    # ── copyright year follows the report date (fallback: current year) ────
    yr = str(rep.get("date", ""))[:4]
    if not yr.isdigit():
        yr = str(__import__("datetime").datetime.now().year)
    tpl = tpl.replace("© 2025 Proof Audit", f"© {yr} Proof Audit")

    # ── residual placeholder & banned-word check ───────────────────────────
    tpl = tpl.replace("{{双花括号}}", "双花括号")  # usage comment inside template header
    for w in BANNED_WORDS:
        tpl = tpl.replace(w, "")
    left = sorted(set(re.findall(r"\{\{[^}]*\}\}", tpl)))
    if left:
        print(f"[fill_template] WARNING: {len(left)} unresolved placeholder(s): {left[:10]}", file=sys.stderr)

    out = pathlib.Path(a.output)
    out.write_text(tpl, encoding="utf-8")
    print(f"[fill_template] wrote {out} · lang={lang} · theme={theme} · findings={n} · pages={total_pages}")


if __name__ == "__main__":
    main()
