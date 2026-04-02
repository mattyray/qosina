"""PDF to image conversion for multimodal AI processing."""

import base64
import io


def pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> list[str]:
    """
    Convert PDF bytes to a list of base64-encoded PNG images (one per page).
    Uses PyMuPDF (fitz) for rendering.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []

    for page in doc:
        # Render page at specified DPI
        zoom = dpi / 72  # 72 is default PDF DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # Convert to PNG bytes then base64
        png_bytes = pix.tobytes("png")
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        images.append(b64)

    doc.close()
    return images
