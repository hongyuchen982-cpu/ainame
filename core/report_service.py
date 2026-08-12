import hashlib
import html
import os
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    KeepTogether,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#24211D")
MUTED = colors.HexColor("#716B62")
RED = colors.HexColor("#A53E32")
GOLD = colors.HexColor("#C99855")
PAPER = colors.HexColor("#F8F5EE")
LINE = colors.HexColor("#DDD5C8")


def _register_fonts() -> tuple[str, str]:
    regular_candidates = [
        os.getenv("PDF_FONT_PATH", ""),
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ]
    bold_candidates = [
        os.getenv("PDF_BOLD_FONT_PATH", ""),
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
    ]
    regular = next(
        (item for item in regular_candidates if item and Path(item).is_file()), None
    )
    bold = next(
        (item for item in bold_candidates if item and Path(item).is_file()), regular
    )
    if regular:
        if "AINamingCN" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("AINamingCN", regular))
        if "AINamingCNBold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("AINamingCNBold", bold))
        return "AINamingCN", "AINamingCNBold"
    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    return "STSong-Light", "STSong-Light"


def _text(value: Any) -> str:
    if value is None or value == "":
        return "未提供"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) or "未提供"
    return str(value)


def _safe(value: Any) -> str:
    return html.escape(_text(value)).replace("\n", "<br/>")


def _styles():
    regular, bold = _register_fonts()
    base = getSampleStyleSheet()
    return {
        "regular_font": regular,
        "bold_font": bold,
        "body": ParagraphStyle(
            "CNBody",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=9.5,
            leading=16,
            textColor=INK,
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "CNSmall",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=7.5,
            leading=12,
            textColor=MUTED,
        ),
        "title": ParagraphStyle(
            "CNTitle",
            parent=base["Title"],
            fontName=bold,
            fontSize=28,
            leading=38,
            alignment=TA_CENTER,
            textColor=INK,
        ),
        "name": ParagraphStyle(
            "CNName",
            parent=base["Title"],
            fontName=bold,
            fontSize=38,
            leading=50,
            alignment=TA_CENTER,
            textColor=RED,
        ),
        "subtitle": ParagraphStyle(
            "CNSubtitle",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=11,
            leading=20,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
        "h1": ParagraphStyle(
            "CNH1",
            parent=base["Heading1"],
            fontName=bold,
            fontSize=18,
            leading=25,
            textColor=INK,
            spaceBefore=4,
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "CNH2",
            parent=base["Heading2"],
            fontName=bold,
            fontSize=12,
            leading=18,
            textColor=RED,
            spaceBefore=10,
            spaceAfter=8,
        ),
        "quote": ParagraphStyle(
            "CNQuote",
            parent=base["BodyText"],
            fontName=regular,
            fontSize=11,
            leading=20,
            leftIndent=12,
            rightIndent=12,
            borderColor=GOLD,
            borderWidth=1,
            borderPadding=12,
            backColor=PAPER,
            textColor=INK,
            spaceAfter=12,
        ),
    }


def _paragraph(value: Any, style) -> Paragraph:
    return Paragraph(_safe(value), style)


def _table(
    rows: list[list[Any]], widths: list[float], styles, header: bool = True
) -> Table:
    data = [
        [
            cell if isinstance(cell, Paragraph) else _paragraph(cell, styles["body"])
            for cell in row
        ]
        for row in rows
    ]
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PAPER),
                ("TEXTCOLOR", (0, 0), (-1, 0), RED),
                ("FONTNAME", (0, 0), (-1, 0), styles["bold_font"]),
            ]
        )
    table.setStyle(TableStyle(commands))
    return table


def _header_footer(canvas, doc, regular_font: str):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, height - 15 * mm, width - 20 * mm, height - 15 * mm)
    canvas.setFont(regular_font, 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, height - 11.5 * mm, "一念 AI · 命名价值报告")
    canvas.drawRightString(width - 20 * mm, 11 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def _build_story(snapshot: dict[str, Any], styles) -> list[Any]:
    project = snapshot["project"]
    selected = snapshot["final_selection"]
    validation = snapshot.get("validation")
    asset = snapshot.get("brand_asset")
    story: list[Any] = [
        Spacer(1, 24 * mm),
        Paragraph("一念 AI 命名价值报告", styles["title"]),
        Spacer(1, 9 * mm),
        Paragraph(_safe(selected["name"]), styles["name"]),
        Spacer(1, 5 * mm),
        Paragraph(_safe(project["title"]), styles["subtitle"]),
        Spacer(1, 24 * mm),
        _paragraph(
            "从命名条件、候选推演到最终选择，再到品牌定位与风险校验，本报告完整保存本次命名决策依据。",
            styles["quote"],
        ),
        Spacer(1, 28 * mm),
        _table(
            [
                ["项目类型", project["category"]],
                ["生成轮次", f"{len(snapshot.get('rounds', []))} 轮"],
                ["报告时间", snapshot["generated_at"]],
                ["报告编号", snapshot["report_reference"]],
            ],
            [38 * mm, 112 * mm],
            styles,
            header=False,
        ),
        PageBreak(),
        Paragraph("01 · 项目与命名条件", styles["h1"]),
    ]
    condition_labels = {
        "surname": "姓氏",
        "gender": "性别",
        "length": "长度",
        "other": "补充诉求",
        "exclude": "排除内容",
        "category": "命名类型",
    }
    conditions = project.get("conditions", {})
    condition_rows = [["条件", "内容"]] + [
        [condition_labels.get(key, key), _text(value)]
        for key, value in conditions.items()
        if value not in (None, "", [])
    ]
    story.extend(
        [
            _table(condition_rows or [["条件", "未提供"]], [38 * mm, 112 * mm], styles),
            Spacer(1, 8 * mm),
        ]
    )
    story.extend(
        [
            Paragraph("02 · 最终选名", styles["h1"]),
            Paragraph(_safe(selected["name"]), styles["name"]),
            Paragraph("名字寓意", styles["h2"]),
            _paragraph(selected.get("moral"), styles["quote"]),
            Paragraph("出处与创作思路", styles["h2"]),
            _paragraph(selected.get("reference"), styles["body"]),
            PageBreak(),
            Paragraph("03 · 候选名称与推演过程", styles["h1"]),
        ]
    )
    for round_item in snapshot.get("rounds", []):
        story.append(Paragraph(f"第 {round_item['round_no']} 轮", styles["h2"]))
        if round_item.get("feedback"):
            story.append(
                _paragraph(f"用户反馈：{round_item['feedback']}", styles["quote"])
            )
        candidate_rows = [["名称", "寓意", "出处/思路", "域名建议"]]
        for candidate in round_item.get("candidates", []):
            domain = " · ".join(
                part
                for part in [
                    candidate.get("domain", ""),
                    candidate.get("domain_status", ""),
                ]
                if part
            )
            candidate_rows.append(
                [
                    candidate["name"],
                    candidate.get("moral"),
                    candidate.get("reference"),
                    domain or "未提供",
                ]
            )
        story.extend(
            [
                _table(candidate_rows, [22 * mm, 47 * mm, 51 * mm, 30 * mm], styles),
                Spacer(1, 7 * mm),
            ]
        )

    story.extend([PageBreak(), Paragraph("04 · 名称校验与风险", styles["h1"])])
    if validation:
        story.extend(
            [
                _table(
                    [
                        ["风险等级", validation.get("risk_level", "unknown")],
                        ["风险评分", str(validation.get("risk_score", "-"))],
                        ["数据覆盖率", f"{validation.get('coverage', 0)}%"],
                        ["风险摘要", validation.get("risk_summary")],
                    ],
                    [38 * mm, 112 * mm],
                    styles,
                    header=False,
                ),
                Paragraph("域名矩阵", styles["h2"]),
            ]
        )
        domains = [["域名", "状态", "建议"]]
        matrix = asset.get("domain_matrix", []) if asset else []
        if matrix:
            domains.extend(
                [
                    [item.get("domain"), item.get("status"), item.get("recommendation")]
                    for item in matrix
                ]
            )
        else:
            domains.extend(
                [
                    [
                        item.get("domain"),
                        item.get("status"),
                        item.get("message", "请人工复核"),
                    ]
                    for item in validation.get("domains", [])
                ]
            )
        story.append(_table(domains, [52 * mm, 28 * mm, 70 * mm], styles))
    else:
        story.append(
            _paragraph(
                "本项目尚未关联名称综合校验。正式使用、申请商标或注册域名前，请完成专业检索与法律核查。",
                styles["quote"],
            )
        )

    story.extend([PageBreak(), Paragraph("05 · 品牌价值资产", styles["h1"])])
    if asset:
        positioning = asset.get("positioning", {})
        story.extend(
            [
                Paragraph("品牌定位说明", styles["h2"]),
                _paragraph(positioning.get("positioning_statement"), styles["quote"]),
                _table(
                    [
                        ["目标受众", positioning.get("target_audience")],
                        ["市场品类", positioning.get("market_category")],
                        ["核心价值", positioning.get("core_value")],
                        ["品牌个性", positioning.get("brand_personality")],
                        ["差异化", positioning.get("differentiation")],
                    ],
                    [38 * mm, 112 * mm],
                    styles,
                    header=False,
                ),
                Paragraph("Slogan 方案", styles["h2"]),
            ]
        )
        slogan_rows = [["Slogan", "语气", "创意解释"]] + [
            [item.get("text"), item.get("tone"), item.get("rationale")]
            for item in asset.get("slogans", [])
        ]
        story.extend(
            [
                _table(slogan_rows, [45 * mm, 24 * mm, 81 * mm], styles),
                Paragraph("Logo 概念方向", styles["h2"]),
            ]
        )
        logo_rows = [["方向", "图形与构图", "色彩与字体"]]
        for item in asset.get("logo_concepts", []):
            logo_rows.append(
                [
                    item.get("title"),
                    f"{_text(item.get('symbol'))}；{_text(item.get('composition'))}",
                    f"{_text(item.get('colors'))}；{_text(item.get('typography'))}",
                ]
            )
        story.append(_table(logo_rows, [30 * mm, 64 * mm, 56 * mm], styles))
        visual = asset.get("visual_guidelines", {})
        visual_block = [
                Paragraph("品牌视觉建议", styles["h2"]),
                _table(
                    [
                        [
                            "品牌色",
                            "；".join(
                                f"{item.get('name')} {item.get('hex')}（{item.get('usage')}）"
                                for item in visual.get("colors", [])
                            ),
                        ],
                        ["字体", visual.get("typography")],
                        ["图像", visual.get("imagery")],
                        ["版式", visual.get("layout")],
                        ["避免", visual.get("avoid")],
                    ],
                    [38 * mm, 112 * mm],
                    styles,
                    header=False,
                ),
        ]
        story.extend([KeepTogether(visual_block), Paragraph("品牌风险行动清单", styles["h2"])])
        risk_rows = [["类别", "等级", "风险与行动建议"]] + [
            [
                item.get("category"),
                item.get("level"),
                f"{_text(item.get('note'))}；建议：{_text(item.get('action'))}",
            ]
            for item in asset.get("risk_notes", [])
        ]
        story.append(_table(risk_rows, [27 * mm, 20 * mm, 103 * mm], styles))
    else:
        story.append(
            _paragraph(
                "本项目尚未生成品牌价值资产。可在“品牌资产”页面生成定位、Slogan、Logo 概念与视觉建议后重新导出报告。",
                styles["quote"],
            )
        )

    story.extend(
        [
            Spacer(1, 12 * mm),
            Paragraph("重要提示", styles["h2"]),
            _paragraph(
                "本报告用于命名与品牌策略辅助，不构成法律意见、商标核准结论、企业名称登记承诺或域名注册保证。正式投入使用前，请咨询具备资质的商标、法律及品牌专业机构。",
                styles["small"],
            ),
        ]
    )
    return story


def generate_naming_report_pdf(
    snapshot: dict[str, Any], output_dir: Path, filename: str
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / filename
    temporary_path = output_dir / f".{filename}.tmp"
    styles = _styles()
    document = SimpleDocTemplate(
        str(temporary_path),
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=22 * mm,
        bottomMargin=19 * mm,
        title=f"{snapshot['final_selection']['name']} - 命名价值报告",
        author="一念 AI",
    )
    try:
        document.build(
            _build_story(snapshot, styles),
            onFirstPage=lambda canvas, doc: _header_footer(
                canvas, doc, styles["regular_font"]
            ),
            onLaterPages=lambda canvas, doc: _header_footer(
                canvas, doc, styles["regular_font"]
            ),
        )
        os.replace(temporary_path, final_path)
        content = final_path.read_bytes()
        return {
            "filename": filename,
            "file_size": len(content),
            "page_count": len(PdfReader(str(final_path)).pages),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    except Exception:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise
