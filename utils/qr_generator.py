"""
CampusBuzz Kenya - QR Code Generator
Generates branded QR codes for WhatsApp group invite links.
"""

import io
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from PIL import Image, ImageDraw, ImageFont
from aiogram.types import BufferedInputFile


# Brand colours
GREEN = (34, 197, 94)    # Tailwind green-500
BLACK = (15, 15, 15)
WHITE = (255, 255, 255)


def generate_group_qr(
    link: str,
    group_name: str,
    university_name: str = "",
) -> BufferedInputFile:
    """
    Generate a branded QR code image for a WhatsApp group.
    Returns an aiogram BufferedInputFile ready to send as a photo.
    """
    # ── QR code ──────────────────────────────────────────────
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(link)
    qr.make(fit=True)

    qr_img: Image.Image = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(
            front_color=BLACK,
            back_color=WHITE,
        ),
    ).convert("RGB")

    qr_size = qr_img.size[0]

    # ── Canvas ────────────────────────────────────────────────
    padding   = 30
    header_h  = 80
    footer_h  = 60
    canvas_w  = qr_size + padding * 2
    canvas_h  = qr_size + padding * 2 + header_h + footer_h

    canvas = Image.new("RGB", (canvas_w, canvas_h), BLACK)
    draw   = ImageDraw.Draw(canvas)

    # Header bar
    draw.rectangle([0, 0, canvas_w, header_h], fill=GREEN)

    # Header text
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        font_lg = ImageFont.load_default()
        font_sm = font_lg

    title = group_name[:38]
    draw.text((padding, 15), title, font=font_lg, fill=WHITE)

    # Paste QR
    canvas.paste(qr_img, (padding, header_h + padding // 2))

    # Footer
    footer_y = header_h + padding // 2 + qr_size + 10
    footer_text = "Powered by CampusBuzz Kenya 🇰🇪"
    draw.text((padding, footer_y), footer_text, font=font_sm, fill=GREEN)

    if university_name:
        draw.text((padding, footer_y + 20), university_name, font=font_sm, fill=WHITE)

    # ── Encode to bytes ───────────────────────────────────────
    buf = io.BytesIO()
    canvas.save(buf, format="PNG", optimize=True)
    buf.seek(0)

    safe_name = "".join(c for c in group_name if c.isalnum() or c in " _-")[:30]
    return BufferedInputFile(buf.read(), filename=f"qr_{safe_name}.png")
