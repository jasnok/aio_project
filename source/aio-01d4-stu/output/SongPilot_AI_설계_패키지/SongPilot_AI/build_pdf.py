"""Rebuild the one-page Korean brief. This is document tooling, not the MVP app."""
from pathlib import Path
from html import escape
import json

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "output" / "pdf" / "SongPilot_AI_프로젝트_기획서_1페이지.pdf"
QA = ROOT / "tmp" / "pdfs" / "songpilot_ai"
DEST.parent.mkdir(parents=True, exist_ok=True)
QA.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont("Malgun", "C:/Windows/Fonts/malgun.ttf"))
pdfmetrics.registerFont(TTFont("MalgunBold", "C:/Windows/Fonts/malgunbd.ttf"))
pdfmetrics.registerFontFamily("Malgun", normal="Malgun", bold="MalgunBold")

W, H = A4
M = 34
CW = W - 2 * M
NAVY = colors.HexColor("#102C41")
TEAL = colors.HexColor("#087F82")
INK = colors.HexColor("#223847")
MUTED = colors.HexColor("#596C78")
LINE = colors.HexColor("#D7E2E8")
PALE = colors.HexColor("#EFF7F8")
C = canvas.Canvas(str(DEST), pagesize=A4)
C.setTitle("SongPilot AI — 기관·기업용 AI 음악 콘텐츠 기획 및 제작 워크플로우")
C.setAuthor("SongPilot AI 프로젝트 기획")
C.setSubject("설계 단계 / 가상 업무 사례 / MVP 구현 목표")
placed = []


def text(x, top, value, size=10.0, color=INK, bold=False):
    C.setFillColor(color)
    C.setFont("MalgunBold" if bold else "Malgun", size)
    C.drawString(x, H - top - size, value)


def para(x, top, width, value, size=10.0, leading=14.8, color=INK,
         max_height=None, bold=False):
    style = ParagraphStyle("body", fontName="MalgunBold" if bold else "Malgun",
                           fontSize=size, leading=leading, textColor=color,
                           wordWrap="CJK", splitLongWords=True)
    p = Paragraph(value, style)
    _, height = p.wrap(width, H)
    if max_height is not None and height > max_height + 0.01:
        raise ValueError(f"Text overflow: {height:.1f}>{max_height}: {value}")
    if top + height > H - 17:
        raise ValueError("Text extends below footer margin")
    p.drawOn(C, x, H - top - height)
    placed.append({"top": top, "bottom": top + height, "height": height,
                   "text": value})
    return height


def line(top, x=M, width=CW):
    C.setStrokeColor(LINE)
    C.setLineWidth(0.6)
    C.line(x, H - top, x + width, H - top)


def heading(x, top, number, label):
    text(x, top, number, size=9, color=TEAL, bold=True)
    text(x + 21, top - 0.7, label, size=11, color=NAVY, bold=True)


# Header
C.setFillColor(NAVY)
C.rect(0, H - 120, W, 120, fill=1, stroke=0)
C.setFillColor(colors.HexColor("#54C3C1"))
C.rect(M, H - 26, 26, 3, fill=1, stroke=0)
text(M + 37, 19, "PROJECT BRIEF  /  2026.10.26", 8.3, colors.HexColor("#BDCFDA"))
text(M, 36, "SongPilot AI", 29.5, colors.white, True)
text(M, 78, "기관·기업용 AI 음악 콘텐츠 기획 및 제작 워크플로우", 12.3, colors.white, True)
text(M, 101, "설계 단계  |  아래 기능은 MVP 구현 목표이며 구현·검증 완료를 의미하지 않음", 8.2,
     colors.HexColor("#D7E7EF"))

heading(M, 135, "01", "문제와 목적")
para(M, 155, CW,
     "공공기관·기업·교육기관은 음악 제작의 목적·대상·필수 문구를 반복 전달하고 수작업으로 검수한다. "
     "요구사항과 검수 결과를 표준화해 누락과 수정 반복을 줄이는 것이 목표다.",
     max_height=45)

# Concrete fictional business case
TOP, HEIGHT = 208, 136
C.setFillColor(PALE)
C.roundRect(M, H - TOP - HEIGHT, CW, HEIGHT, 9, fill=1, stroke=0)
C.setFillColor(TEAL)
C.roundRect(M + 14, H - TOP - 31, 92, 20, 4, fill=1, stroke=0)
text(M + 24, TOP + 14, "가상 업무 사례", 9.5, colors.white, True)
text(M + 118, TOP + 16, "특정 기관의 실제 도입 사례가 아닙니다", 8.5, MUTED)
text(M + 15, TOP + 42, "사용자  지자체 시민안전 홍보팀", 10.6, NAVY, True)
para(M + 15, TOP + 64, CW - 30,
     "“여름철 폭염 예방 캠페인용 <b>30초 홍보 음악</b>을 기획해 주세요. "
     "어르신도 이해하기 쉬운 밝고 신뢰감 있는 분위기, 쉬운 한국어를 사용해 주세요.”",
     size=10.5, leading=15.7, max_height=48)
text(M + 15, TOP + 116, "필수 메시지  물 마시기 · 그늘 이용 · 낮 시간 야외활동 자제", 9.6, TEAL, True)

# Middle: responsibilities and deliverables
COL_TOP = 359
LEFT = 310
GAP = 20
RIGHT_X = M + LEFT + GAP
RIGHT_W = CW - LEFT - GAP
heading(M, COL_TOP, "02", "AI 처리와 실패 분기")
steps = [
    ("1  기획", "목적·대상·채널·필수 조건 구조화"),
    ("2  가사", "쉬운 한국어, 짧은 후렴·반복구 작성"),
    ("3  스타일", "장르·템포·보컬·악기를 Style Prompt로 변환"),
    ("4  검수", "코드로 문구·형식, AI로 의미·명확성 점검"),
    ("5  분기", "최대 2회 수정, 상충·불확실·초과 시 확인"),
    ("6  승인", "담당자가 해당 버전의 제작 패키지를 검토"),
]
for i, (label, body) in enumerate(steps):
    yy = COL_TOP + 25 + i * 23
    text(M, yy, label, 9.2, TEAL, True)
    para(M + 59, yy + 0.5, LEFT - 59, escape(body), size=9.1, leading=12.3,
         max_height=13)

C.setStrokeColor(LINE)
C.setLineWidth(0.7)
C.line(RIGHT_X - 11, H - COL_TOP - 6, RIGHT_X - 11, H - COL_TOP - 164)
heading(RIGHT_X, COL_TOP, "03", "결과물과 차별점")
para(RIGHT_X, COL_TOP + 25, RIGHT_W,
     "<b>가사 초안</b><br/><b>Suno Style Prompt</b><br/>검수 체크리스트<br/>JSON·Markdown / 수정 이력",
     size=9.7, leading=16.2, max_height=65)
para(RIGHT_X, COL_TOP + 102, RIGHT_W,
     "역할별 데이터 계약과 상태 추적<br/>필수 문구의 정확 일치·의미 검수<br/>실패 원인·재시도·승인 버전 기록",
     size=9.0, leading=14.5, color=MUTED, max_height=59)

line(536)
heading(M, 548, "04", "최소 기술 구성")
para(M, 569, CW,
     "<b>Python · LangGraph · Pydantic · Streamlit · LLM API 1종 · JSON 저장 · pytest</b>",
     size=10, leading=14, max_height=14)
para(M, 588, CW,
     "동일 LLM에 역할별 계약 적용. RAG는 기관 문서 검색 필요 시, Docker는 핵심 기능 확인 후 도입.",
     size=9.1, leading=13.3, color=MUTED, max_height=27)

heading(M, 621, "05", "MVP 구현 범위")
para(M, 642, CW,
     "<b>포함</b>  단일 캠페인·트랙의 입력, 분리 생성, 검수·수정·승인, 저장·불러오기와 실행 이력<br/>"
     "<b>제외</b>  실제 음원 생성·마스터링, 자동 게시, 기관 내부 시스템 연동. 여러 트랙은 후속 확장.",
     size=9.5, leading=15.4, max_height=46.3)

heading(M, 697, "06", "완료 기준")
para(M, 718, CW,
     "① 가사·Style Prompt 분리 패키지 생성  ② 누락·형식 오류 탐지 및 수정·사용자 확인 분기<br/>"
     "③ JSON·Markdown 저장·불러오기, 단계별 상태·검수·이력 확인  ④ 정상·실패·재시도·승인 테스트",
     size=9.2, leading=15.3, max_height=46)

line(772)
para(M, 781, CW,
     "<b>목표 30초 / 실제 음원 길이 미검증.</b> 패키지 승인 후 외부 도구에서 활용하며, 최종 음원·게시·방송은 별도 승인.",
     size=8.2, leading=12.4, color=MUTED, max_height=25)
text(M, 811, "레퍼런스  Wavenox Suno Command Maker", 7.8, MUTED)
URL = "https://free.wavenox.com/tools/suno-command-maker/"
URL_X = M + 194
text(URL_X, 811, URL, 7.4, TEAL)
C.linkURL(URL, (URL_X, H - 822, URL_X + pdfmetrics.stringWidth(URL, "Malgun", 7.4), H - 809),
          relative=0, thickness=0)
C.showPage()
C.save()

reader = PdfReader(str(DEST))
assert len(reader.pages) == 1, "PDF must contain exactly one page"
page = reader.pages[0]
assert abs(float(page.mediabox.width) - W) < 0.1
assert abs(float(page.mediabox.height) - H) < 0.1
extracted = page.extract_text()
required = ["SongPilot AI", "기관·기업용", "가상 업무 사례", "폭염", "물 마시기", "그늘 이용",
            "낮 시간 야외활동 자제", "LangGraph", "완료 기준", "미검증", URL]
for token in required:
    assert token in extracted, f"Missing extracted text: {token}"
assert "\ufffd" not in extracted
(QA / "extracted.txt").write_text(extracted, encoding="utf-8")
(QA / "layout.json").write_text(json.dumps(placed, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"pdf": str(DEST), "pages": len(reader.pages), "a4": True,
                  "required_text_checks": len(required), "file_bytes": DEST.stat().st_size}, ensure_ascii=False))
