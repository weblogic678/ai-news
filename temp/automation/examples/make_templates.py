"""Create original Excalidraw templates; no third-party graphics or fonts bundled."""
import json
from pathlib import Path


def base(kind, ident, x, y, width, height, color="#1971c2", background="#e7f5ff"):
    return {"id": ident, "type": kind, "x": x, "y": y, "width": width, "height": height,
            "angle": 0, "strokeColor": color, "backgroundColor": background,
            "fillStyle": "solid", "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1,
            "opacity": 100, "groupIds": [], "frameId": None, "roundness": {"type": 3} if kind == "rectangle" else None,
            "seed": sum(map(ord, ident)) * 19, "version": 1, "versionNonce": sum(map(ord, ident)) * 23,
            "isDeleted": False, "boundElements": None, "updated": 0, "link": None, "locked": False}


def text(ident, x, y, value, size=24, width=190):
    element = base("text", ident, x, y, width, size * 1.25, "#1e293b", "transparent")
    element.update(text=value, originalText=value, fontSize=size, fontFamily=2,
                   textAlign="center", verticalAlign="middle", containerId=None,
                   autoResize=True, lineHeight=1.25)
    return element


def scene(name, boxes, links):
    elements = [text("title", 380, 70, name, 32, 380)]
    for index, (label, x, y) in enumerate(boxes):
        elements.append(base("rectangle", f"box-{index}", x, y, 220, 80))
        elements.append(text(f"label-{index}", x+15, y+25, label))
    for index, (start, end) in enumerate(links):
        sx, sy = boxes[start][1]+110, boxes[start][2]+80
        ex, ey = boxes[end][1]+110, boxes[end][2]
        if abs(sy-ey) < 10:
            sx, sy = boxes[start][1]+220, boxes[start][2]+40
            ex, ey = boxes[end][1], boxes[end][2]+40
        arrow = base("arrow", f"arrow-{index}", sx, sy, abs(ex-sx), abs(ey-sy), "#64748b", "transparent")
        arrow.update(points=[[0,0],[ex-sx,ey-sy]], startBinding=None, endBinding=None,
                     lastCommittedPoint=None, startArrowhead=None, endArrowhead="arrow", elbowed=False)
        elements.append(arrow)
    elements.append(text("footer", 370, 850, "原创模板 · 节点和文字可编辑", 18, 400))
    return {"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": elements,
            "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"}, "files": {}}


def create(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    templates = {
        "01-approval-flow": scene("需求审批流程", [("提交需求",460,160),("资料检查",460,300),("技术评估",250,460),("预算评估",670,460),("确认与归档",460,650)],[(0,1),(1,2),(1,3),(2,4),(3,4)]),
        "02-deployment-flow": scene("开源工具部署流程", [("确认环境",460,160),("获取官方版本",460,300),("配置与安装",460,440),("样例验收",460,580),("备份与交付",460,720)],[(0,1),(1,2),(2,3),(3,4)]),
        "03-backup-plan": scene("文件备份检查流程", [("选择文件副本",460,160),("计算校验值",460,300),("保存至备份目录",250,460),("记录版本清单",670,460),("恢复与一致性检查",460,650)],[(0,1),(1,2),(1,3),(2,4),(3,4)]),
    }
    for name, value in templates.items():
        (folder / (name + ".excalidraw")).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return list(templates)


if __name__ == "__main__":
    print(create(Path(__file__).parent / "excalidraw-templates"))
