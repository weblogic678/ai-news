"""Optional marketplace PNG cards. Requires Pillow and a user-supplied CJK font."""
from pathlib import Path
from .catalog import product


def render(repo, folder, font_path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ValueError("PNG生成需要Pillow：python -m pip install Pillow；其他核心功能无此依赖") from None
    font_path = Path(font_path)
    if not font_path.is_file():
        raise ValueError("中文字体文件不存在；Windows可使用C:/Windows/Fonts/msyh.ttc")
    p = product(repo)
    images = Path(folder) / "images"
    images.mkdir(parents=True, exist_ok=True)
    def font(size):
        return ImageFont.truetype(str(font_path), size)
    for index, subtitle in enumerate(("原创材料与服务", "交付内容说明", "免费来源与使用边界"), 1):
        image = Image.new("RGB", (1080, 1080), "#edf2f6")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((40, 40, 1040, 1040), radius=36, fill="white")
        draw.text((80, 90), "待审核草稿 · 商品说明图", font=font(27), fill="#80591c")
        draw.text((80, 200), p["name"], font=font(52), fill="#17364f")
        draw.text((80, 300), subtitle, font=font(34), fill="#42677b")
        rows = p["features"][:3] or ["功能待验证", "交付内容待定义", "平台类目待核对"]
        for row, text in enumerate(rows):
            # Wrap conservatively by rendered width instead of truncating claims.
            lines, line = [], ""
            for char in text:
                if draw.textlength(line + char, font=font(29)) > 840:
                    lines.append(line); line = char
                else:
                    line += char
            lines.append(line)
            y = 435 + row * 120
            for offset, line in enumerate(lines[:2]):
                draw.text((110, y + offset * 38), line, font=font(29), fill="#243c52")
        draw.text((80, 830), "软件与公开资料可免费获取", font=font(28), fill="#42677b")
        draw.text((80, 890), "收费内容须明确，功能和环境须实测", font=font(26), fill="#80591c")
        draw.text((80, 970), "基于 " + p["repo"], font=font(23), fill="#687b89")
        dest = images / f"listing-{index}.png"
        if dest.exists():
            raise ValueError("PNG已存在，不覆盖人工修改：" + str(dest))
        image.save(dest)
    return images
