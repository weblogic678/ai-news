from pathlib import Path
from datetime import datetime
import pdf_batch
base=Path(__file__).resolve().parent
dest=base/'runtime'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')/'merged.pdf'
dest.parent.mkdir(parents=True)
try:
    pdf_batch.process('merge',base/'samples',dest,'pdfcpu')
    print('Created:',dest)
except pdf_batch.ToolError as error:
    print(error)
    raise SystemExit(1)
