"""Generate a stable UTF-8 PDF fixture for visual report QA."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.report_service import generate_naming_report_pdf


def preview_snapshot() -> dict:
    candidates = [
        {"name": "并发星", "reference": "群星并行", "moral": "协同进取", "domain": "concurrent-star.com", "domain_status": "已注册"},
        {"name": "合序", "reference": "和合有序", "moral": "清晰协作", "domain": "hexu.cn", "domain_status": "可能可注册"},
        {"name": "启衡", "reference": "启新守衡", "moral": "创新稳健", "domain": "qiheng.com", "domain_status": "待复核"},
    ]
    return {
        "report_reference": "REPORT-QA-20260811",
        "generated_at": "2026-08-11 21:30:00",
        "project": {"id": 1, "title": "东方智能协作品牌命名", "category": "企业名", "status": "selected", "conditions": {"category": "企业名", "length": "两字", "other": "面向成长型科技企业，强调协作、可信与东方审美", "exclude": ["智", "云"]}, "created_at": "2026-08-11"},
        "final_selection": {"id": 1, "name": "并发星", "reference": "取群星并行、汇聚成光的协作意象", "moral": "多方智慧并行汇聚，以稳定节奏共同抵达目标", "logo_url": ""},
        "rounds": [
            {"round_no": 1, "feedback": "", "created_at": "2026-08-11", "candidates": candidates},
            {"round_no": 2, "feedback": "希望更有未来感，同时保持可信与克制", "created_at": "2026-08-11", "candidates": candidates[:2]},
        ],
        "validation": {"id": 1, "risk_score": 62, "risk_level": "medium", "coverage": 100, "risk_summary": "存在同类近似名称，主域名已注册，建议进一步商标检索。", "domains": [{"domain": "concurrent-star.com", "status": "registered", "message": "已注册"}, {"domain": "concurrent-star.cn", "status": "available", "message": "可能可注册"}], "created_at": "2026-08-11"},
        "brand_asset": {
            "id": 1,
            "positioning": {"target_audience": "重视效率与品牌表达的成长型科技企业", "market_category": "企业智能协作服务", "core_value": "让复杂协作清晰发生", "brand_personality": ["清晰", "可信", "进取"], "differentiation": "融合东方语义与智能流程", "positioning_statement": "面向成长型企业，以东方秩序感重塑智能协作体验。"},
            "slogans": [{"text": "并发灵感，共赴新程", "tone": "进取", "rationale": "呼应名称与协作价值"}, {"text": "让每一步，同频向前", "tone": "温暖", "rationale": "强调团队一致行动"}, {"text": "汇聚所想，成就所向", "tone": "稳健", "rationale": "表达聚合与兑现"}],
            "logo_concepts": [{"title": "星轨汇聚", "symbol": "多条轨迹汇聚成星", "composition": "横向组合标", "colors": ["深海蓝", "晨曦金"], "typography": "现代无衬线字体"}, {"title": "并行之门", "symbol": "双线构成开放门户", "composition": "方形图标加字标", "colors": ["墨黑", "活力红"], "typography": "几何黑体"}],
            "visual_guidelines": {"colors": [{"name": "深海蓝", "hex": "#173B57", "usage": "主品牌色"}, {"name": "晨曦金", "hex": "#D99B5E", "usage": "强调色"}, {"name": "云白", "hex": "#F8F6F1", "usage": "背景色"}], "typography": "标题采用现代黑体，正文注重屏幕易读性", "imagery": "轨迹、光点与真实团队协作场景", "layout": "充足留白与模块化网格", "avoid": ["过度科技蓝", "复杂渐变", "未经核实的认证标识"]},
            "domain_matrix": [{"domain": "concurrent-star.com", "status": "registered", "recommendation": "评估替代拼写或其他后缀"}, {"domain": "concurrent-star.cn", "status": "available", "recommendation": "优先注册并配置品牌保护"}],
            "risk_notes": [{"category": "品牌辨识", "level": "medium", "note": "名称包含常见星意象", "action": "强化独特图形资产"}, {"category": "使用合规", "level": "high", "note": "校验发现近似项", "action": "申请前咨询商标专业人士"}],
            "created_at": "2026-08-11",
        },
    }


if __name__ == "__main__":
    result = generate_naming_report_pdf(
        preview_snapshot(),
        ROOT / "output" / "pdf",
        "sample-naming-report.pdf",
    )
    print(result)
