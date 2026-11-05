from pathlib import Path
import json
import re
import unicodedata
from xml.sax.saxutils import escape

from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).parent
raw = unicodedata.normalize('NFC', (ROOT / 'essay_draft.txt').read_text(encoding='utf-8').strip())
blocks = re.split(r'\n\s*\n', raw)
title, paras = blocks[0].strip(), [p.replace('\n', '').strip() for p in blocks[1:]]
body = '\n'.join(paras)
final_text = title + '\n\n' + body
(ROOT / '최종원고.txt').write_text(final_text, encoding='utf-8', newline='\n')

counts = {
    'counting_method': 'Unicode NFC code points; spaces and punctuation included; CRLF normalized to LF',
    'title_including_spaces': len(title),
    'body_including_spaces_excluding_linebreaks': sum(map(len, paras)),
    'title_and_body_including_spaces_excluding_linebreaks': len(title) + sum(map(len, paras)),
    'body_including_spaces_and_LF_linebreaks': len(body),
    'entire_txt_including_spaces_and_LF_linebreaks': len(final_text),
    'entire_txt_including_spaces_and_CRLF_linebreaks': len(final_text.replace('\n', '\r\n')),
    'paragraph_count': len(paras),
}
assert max(counts[k] for k in counts if k != 'counting_method') < 3000

pdfmetrics.registerFont(TTFont('Malgun', r'C:\Windows\Fonts\malgun.ttf'))
font_size, leading = 11, 17.6
style = ParagraphStyle('EssayBody', fontName='Malgun', fontSize=font_size, leading=leading,
                       spaceBefore=0, spaceAfter=0, firstLineIndent=11, wordWrap='CJK',
                       allowWidows=0, allowOrphans=0, splitLongWords=1)
title_style = ParagraphStyle('EssayTitle', fontName='Malgun', fontSize=11, leading=17.6,
                             spaceBefore=0, spaceAfter=0, wordWrap='CJK')
label_style = ParagraphStyle('Label', parent=title_style, alignment=1)

table_width = 172.72 * mm
cell_padding = 1.79917 * mm
pdf_path = ROOT / '최종원고_규격확인.pdf'
doc = SimpleDocTemplate(str(pdf_path), pagesize=A4,
                        leftMargin=(A4[0]-table_width)/2+cell_padding-6,
                        rightMargin=(A4[0]-table_width)/2+cell_padding-6,
                        topMargin=25.4*mm-6,
                        bottomMargin=25.4*mm-6,
                        title=title, author='', subject='학습수기')
contents = [Paragraph(escape(p), style) for p in paras]
table = Table([[Paragraph('【 학습수기 】', label_style), ''],
               [Paragraph('제 목', label_style), Paragraph(escape(title), title_style)]],
              colWidths=[20.46817*mm, table_width-20.46817*mm],
              rowHeights=[8.22325*mm, 8.22325*mm], hAlign='CENTER')
table.setStyle(TableStyle([
    ('SPAN', (0,0), (1,0)),
    ('GRID', (0,0), (-1,-1), 0.45, '#000000'),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('VALIGN', (0,0), (-1,0), 'MIDDLE'),
    ('LEFTPADDING', (0,0), (-1,-1), cell_padding),
    ('RIGHTPADDING', (0,0), (-1,-1), cell_padding),
    ('TOPPADDING', (0,0), (-1,-1), 0.49742*mm),
    ('BOTTOMPADDING', (0,0), (-1,-1), 0.49742*mm),
]))
doc.build([table] + contents)
reader = PdfReader(str(pdf_path))
counts['pdf_page_count'] = len(reader.pages)
counts['pdf_page_size_mm'] = [[round(float(p.mediabox.width)/mm,2), round(float(p.mediabox.height)/mm,2)] for p in reader.pages]
counts['format'] = {'font':'맑은 고딕', 'font_size_pt':font_size, 'line_spacing_percent':160,
                    'leading_pt':leading, 'paragraph_before_pt':0, 'paragraph_after_pt':0,
                    'table_width_mm':172.72, 'cell_horizontal_padding_mm':1.799}
assert len(reader.pages) <= 2
pdf_text = ''.join(p.extract_text() or '' for p in reader.pages)
normalize = lambda s: re.sub(r'\s+', '', s)
assert normalize(title) in normalize(pdf_text)
assert normalize(''.join(paras)) in normalize(pdf_text)
assert '\ufffd' not in pdf_text

qa = ROOT / 'qa'
qa.mkdir(exist_ok=True)
pdf = pdfium.PdfDocument(str(pdf_path))
for i in range(len(pdf)):
    page = pdf[i]
    page.render(scale=1.75).to_pil().save(qa / f'page-{i+1}.png')
counts['pdf_text_matches_final_body'] = True
(qa / 'validation.json').write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(counts, ensure_ascii=False, indent=2))
