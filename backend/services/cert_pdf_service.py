"""证书 PDF 生成服务（reportlab）

封装两类输出：
- render_certificate_pdf(data) -> BytesIO  单张证书 PDF
- render_batch_zip(project_id) -> BytesIO  按项目批量打包 ZIP

样式固定为蓝色配色（#4F6EF7 装饰色 / #F8FAFB 背景）+ formal 风格表彰语。
"""
import os
import zipfile
from datetime import datetime
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from services import certificate_service


# ==================== 固定样式常量 ====================

BG_COLOR = '#F8FAFB'
ACCENT_COLOR = '#4F6EF7'
SIGNATURE_TEXT = '高校青年志愿者服务中心'
COMMENDATION_TEXT = (
    '该同学在本次志愿服务活动中表现优秀，认真履行职责，圆满完成各项任务，'
    '展现了良好的责任意识与服务精神，特此证明。'
)


# ==================== 中文字体注册 ====================

_FONT_REGISTERED = False


def _ensure_fonts():
    """注册中文字体（仅注册一次）。在常见 Windows 字体路径中找 SimSun / SimHei。"""
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return

    candidates_song = [
        r'C:\Windows\Fonts\simsun.ttc',
        '/usr/share/fonts/truetype/arphic/uming.ttc',
        '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
    ]
    candidates_hei = [
        r'C:\Windows\Fonts\simhei.ttf',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
    ]

    for path in candidates_song:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('CertSong', path))
                break
            except Exception:
                continue

    for path in candidates_hei:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('CertHei', path))
                break
            except Exception:
                continue

    _FONT_REGISTERED = True


def _font(prefer_hei=False):
    """根据是否注册成功返回可用字体名，回退到内置 Helvetica。"""
    _ensure_fonts()
    if prefer_hei and 'CertHei' in pdfmetrics.getRegisteredFontNames():
        return 'CertHei'
    if 'CertSong' in pdfmetrics.getRegisteredFontNames():
        return 'CertSong'
    return 'Helvetica'


# ==================== 单张证书渲染 ====================

def render_certificate_pdf(data, commendation_text=None):
    """根据证书数据生成单张 PDF，返回 BytesIO。

    data: dict 来自 certificate_service.get_certificate_data()
    commendation_text: 可选的自定义表彰语（如 AI 生成内容）；为空时使用预设文案
    """
    _ensure_fonts()

    buf = BytesIO()
    page_size = landscape(A4)
    width, height = page_size
    c = canvas.Canvas(buf, pagesize=page_size)

    bg = HexColor(BG_COLOR)
    accent = HexColor(ACCENT_COLOR)

    # 背景填充
    c.setFillColor(bg)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # 装饰边框（双层）
    c.setStrokeColor(accent)
    c.setLineWidth(3)
    c.rect(30, 30, width - 60, height - 60, fill=0, stroke=1)
    c.setLineWidth(1)
    c.rect(40, 40, width - 80, height - 80, fill=0, stroke=1)

    # 标题
    c.setFillColor(accent)
    c.setFont(_font(prefer_hei=True), 36)
    c.drawCentredString(width / 2, height - 110, '志愿服务证明')

    # 标题下方装饰条
    c.rect(width / 2 - 80, height - 130, 160, 3, fill=1, stroke=0)

    # 正文：事实段 + 表彰语段（两段连续文本，自动换行）
    user_name = data.get('userName', '')
    student_id = data.get('studentId', '')
    college = data.get('college', '')
    major = data.get('major', '')
    project_title = data.get('projectTitle', '')
    duration = data.get('durationHours', 0)
    sign_in_time = data.get('signInTime', '')

    fact_text = (
        f'兹证明 {user_name} 同学（学号：{student_id}），'
        f'系 {college} {major} 专业学生，'
        f'于 {sign_in_time} 参加了"{project_title}"志愿服务活动，'
        f'累计服务时长 {duration} 小时。'
    )

    # 表彰语：优先使用调用方传入的自定义文本（如 AI 生成），否则回退到预设
    commendation = (commendation_text or '').strip() or COMMENDATION_TEXT

    body_font = _font(prefer_hei=False)
    c.setFillColor(HexColor('#333333'))

    # 事实段
    c.setFont(body_font, 14)
    y = _draw_wrapped(c, fact_text, x=110, y=height - 200,
                      max_width=width - 220, line_height=30)

    # 段间空白
    y -= 14

    # 表彰语段（字号略小）
    c.setFont(body_font, 13)
    _draw_wrapped(c, commendation, x=110, y=y,
                  max_width=width - 220, line_height=24)

    # 签发单位与日期（右下角）
    sign_x = width - 240
    sign_y = 120
    c.setFillColor(accent)
    c.setFont(_font(prefer_hei=True), 14)
    c.drawString(sign_x, sign_y + 30, SIGNATURE_TEXT)

    c.setFillColor(HexColor('#666666'))
    c.setFont(body_font, 12)
    c.drawString(sign_x, sign_y, datetime.now().strftime('%Y 年 %m 月 %d 日'))

    # 圆形盖章占位（虚线圆环）
    c.setStrokeColor(accent)
    c.setLineWidth(1.5)
    c.setDash(2, 2)
    c.circle(width - 110, sign_y + 15, 36, stroke=1, fill=0)
    c.setDash()
    c.setFillColor(accent)
    c.setFont(_font(prefer_hei=True), 9)
    c.drawCentredString(width - 110, sign_y + 12, '盖章处')

    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def _draw_wrapped(c, text, x, y, max_width, line_height):
    """简单的中文文本自动换行（按字符宽度估算）。返回换行后的最终 y 坐标。"""
    if not text:
        return y
    chars = []
    line_width = 0
    avg_w = c._fontsize * 0.95  # 中文字符近似全角宽度
    for ch in text:
        w = avg_w if ord(ch) > 127 else c._fontsize * 0.5
        if line_width + w > max_width and chars:
            c.drawString(x, y, ''.join(chars))
            y -= line_height
            chars = [ch]
            line_width = w
        else:
            chars.append(ch)
            line_width += w
    if chars:
        c.drawString(x, y, ''.join(chars))
        y -= line_height
    return y


# ==================== 批量证书打包 ====================

def render_batch_zip(project_id):
    """按项目批量生成所有合格学生证书并打包 ZIP。返回 (BytesIO, filename)。"""
    eligible = certificate_service.get_eligible_users(project_id)
    if not eligible:
        raise ValueError('该项目暂无符合证书条件的学生（需要已确认打卡记录）')

    zip_buf = BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for user_id in eligible:
            try:
                data = certificate_service.get_certificate_data(user_id, project_id)
            except ValueError:
                continue
            pdf_buf = render_certificate_pdf(data)
            safe_name = data['userName'].replace('/', '_').replace('\\', '_')
            zf.writestr(f"{safe_name}_{data['studentId']}.pdf", pdf_buf.getvalue())

    zip_buf.seek(0)
    project_title = eligible and certificate_service.get_certificate_data(
        eligible[0], project_id
    )['projectTitle'] or 'project'
    safe_title = project_title.replace('/', '_').replace('\\', '_')
    return zip_buf, f'{safe_title}_证书批量导出.zip'
