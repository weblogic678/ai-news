import hashlib
import json
import re
from datetime import datetime, timezone

KNOWN = {
    "MIT": "保留完整许可文本和版权声明；另外审核素材、依赖及商标。",
    "Apache-2.0": "保留许可、版权及适用NOTICE；修改文件按要求标记；另外审核依赖和素材。",
    "BSD-2-Clause": "保留版权、许可条件和免责声明；另查依赖。",
    "BSD-3-Clause": "保留版权、许可条件和免责声明；不得未经许可借作者名义背书。",
}


def fingerprint(value):
    # Capture time is not a material change; source content, inventory and release are.
    core = {k: v for k, v in value.items() if k != "fetched_at"}
    return hashlib.sha256(json.dumps(core, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def detect_license(text):
    # Presence of a name in a README is insufficient. Only inspect captured license text.
    if "Apache License" in text and "Version 2.0" in text and "Redistribution" in text:
        return "Apache-2.0"
    if "Permission is hereby granted, free of charge" in text and "THE SOFTWARE IS PROVIDED" in text:
        return "MIT"
    if "GNU AFFERO GENERAL PUBLIC LICENSE" in text:
        return "AGPL-family"
    if "GNU LESSER GENERAL PUBLIC LICENSE" in text:
        return "LGPL-family"
    if "GNU GENERAL PUBLIC LICENSE" in text:
        return "GPL-family"
    return None


def audit(snapshot):
    declared = (snapshot["metadata"].get("license") or {}).get("spdx_id")
    evidence = snapshot.get("license_files", [])
    main = [f for f in evidence if re.match(r"(?i)^(license|licence|copying)(\.|$)", f["path"])]
    detected = sorted(set(filter(None, (detect_license(x["text"]) for x in main))))
    issues = []
    if not main:
        issues.append("没有取得根目录许可证正文，停止商业发布")
    if len(detected) != 1:
        issues.append("许可证未识别或存在多许可，需要人工审核")
    if len(detected) == 1 and declared and declared not in ("NOASSERTION", "OTHER"):
        compatible = declared == detected[0] or declared.startswith(detected[0].replace("-family", "") + "-")
        if not compatible:
            issues.append("GitHub许可标签与正文识别不一致")
    if snapshot.get("tree_truncated") or not snapshot.get("root_evidence_complete"):
        issues.append("文件清单或根目录许可证据不完整")
    if snapshot["metadata"].get("archived"):
        issues.append("项目已归档，维护风险需要复核")
    detected_one = detected[0] if len(detected) == 1 else "UNKNOWN"
    if detected_one not in KNOWN:
        issues.append("非首期宽松许可白名单，须逐项评估许可义务")
    indicators = [p for p in snapshot.get("tree", []) if re.search(r"(?i)(license|notice|third.party|package.*json$|go\.(mod|sum)$|pubspec|cargo.lock|requirements|fonts?/|vendor/)", p)]
    return {"repo": snapshot["repo"], "sha": snapshot["sha"], "version": snapshot["version"],
            "fingerprint": fingerprint(snapshot), "declared": declared, "detected": detected,
            "status": "blocked" if issues else "preliminary_only", "issues": issues,
            "obligations": KNOWN.get(detected_one, "逐项人工确认；缺失许可不能默认商业分发。"),
            "dependency_indicators": indicators, "dependency_audit_complete": False,
            "commercial_approval": False,
            "note": "自动识别仅为初筛；宽松主许可证不代表全部文件或计划商品已获授权。"}


REVIEW_CHECKS = ["main_license", "dependencies_and_assets", "delivery_scope", "functional_tests", "target_platform", "marketplace_category", "honest_listing", "support_scope", "ai_content"]


def review_template(snapshot, product, digest):
    return {"repo": snapshot["repo"], "sha": snapshot["sha"], "fingerprint": fingerprint(snapshot),
            "bundle_digest": digest, "delivery_mode": "original_materials_only",
            "reviewer": "", "approved_at": "", "checks": {x: False for x in REVIEW_CHECKS},
            "evidence": {x: "" for x in REVIEW_CHECKS}, "approved": False,
            "note": "逐项记录实际证据后再批准；原创材料交付模式也需审核引用及平台类目，不可一键全勾。"}


def validate_review(review, snapshot, digest):
    errors = []
    if review.get("fingerprint") != fingerprint(snapshot) or review.get("sha") != snapshot["sha"]:
        errors.append("来源版本或证据已变化，原审核失效")
    if review.get("bundle_digest") != digest:
        errors.append("交付内容已变化，原审核失效")
    if review.get("delivery_mode") != "original_materials_only":
        errors.append("首期仅支持自编材料交付；上游源码/二进制分发需要另行开发审核流程")
    if not review.get("approved") or not str(review.get("reviewer", "")).strip():
        errors.append("缺少批准或审核人")
    for key in REVIEW_CHECKS:
        if review.get("checks", {}).get(key) is not True or not str(review.get("evidence", {}).get(key, "")).strip():
            errors.append("未完成审核并记录证据：" + key)
    try:
        at = datetime.fromisoformat(review.get("approved_at", ""))
        if at.tzinfo is None or at > datetime.now(timezone.utc):
            errors.append("批准时间须带时区且不能在未来")
    except (ValueError, TypeError):
        errors.append("缺少有效批准时间，例如2026-10-11T12:00:00+08:00")
    return errors
