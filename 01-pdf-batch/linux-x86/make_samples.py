"""Generate two original, single-page test PDFs without third-party dependencies."""
from pathlib import Path


def sample(text):
    if not text.isascii() or any(c in text for c in "()\\"):
        raise ValueError("sample text must be simple ASCII")
    stream = f"BT /F1 20 Tf 72 720 Td ({text}) Tj ET\n".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"endstream",
    ]
    content = b"%PDF-1.4\n"
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(content)
    content += f"xref\n0 {len(objects)+1}\n".encode() + b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n".encode()
    content += f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return content


if __name__ == "__main__":
    folder = Path(__file__).parent / "samples"
    folder.mkdir(exist_ok=True)
    for i in (1, 2):
        with (folder / f"0{i}-demo.pdf").open("xb") as file:
            file.write(sample(f"Original demonstration page {i}"))
    print(folder)
