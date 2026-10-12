from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageOps, UnidentifiedImageError
from rapidocr import RapidOCR
from flask import Response
import csv
import io
import os
import re


app = Flask(__name__)

# Maximum upload size: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "bmp", "tiff", "webp"
}

# Initialize OCR once when the application starts.
ocr_engine = RapidOCR()

# Adjust this if chat rows are merged or split incorrectly.
ROW_GAP_RATIO = 0.022


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def remove_timestamps(text):
    """Remove timestamps such as 9:29 am and 9.29 am."""

    text = re.sub(
        r"\b\d{1,2}[:.]\d{2}\s*(?:am|pm)?\b",
        "",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


def extract_text_from_image(image_bytes):
    """Extract text and bounding boxes using RapidOCR."""

    with Image.open(io.BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    image.thumbnail((1800, 1800))

    result = ocr_engine(image)

    if not result or not result.txts:
        return []

    detections = []

    for box, text in zip(result.boxes, result.txts):
        if not text or not text.strip():
            continue

        xs = [point[0] for point in box]
        ys = [point[1] for point in box]

        detections.append({
            "text": text.strip(),
            "x": min(xs),
            "y": min(ys),
            "right": max(xs),
            "bottom": max(ys),
            "center_y": sum(ys) / len(ys),
            "height": max(ys) - min(ys)
        })

    return detections, image.height


def group_into_lines(detections):
    """Group OCR detections that belong to the same text line."""

    detections = sorted(
        detections,
        key=lambda item: item["center_y"]
    )

    lines = []

    for item in detections:
        matching_line = None

        # Search recent lines for a similar vertical position.
        for line in reversed(lines):
            line_center = sum(
                entry["center_y"] for entry in line
            ) / len(line)

            average_height = sum(
                max(entry["height"], 1) for entry in line
            ) / len(line)

            tolerance = max(8, average_height * 0.65)

            if abs(item["center_y"] - line_center) <= tolerance:
                matching_line = line
                break

            if item["center_y"] - line_center > tolerance:
                break

        if matching_line is None:
            lines.append([item])
        else:
            matching_line.append(item)

    output = []

    for line in lines:
        line.sort(key=lambda item: item["x"])

        output.append({
            "text": " ".join(item["text"] for item in line),
            "y": sum(item["center_y"] for item in line)
                 / len(line),
            "height": max(
                item["height"] for item in line
            )
        })

    return output


def extract_chats_from_lines(lines, image_height):
    """
    Group text lines into chat rows.

    Assumption:
    A typical WhatsApp chat entry has a contact name
    followed by a message preview on the next line.
    """

    if not lines:
        return []

    row_gap = max(18, image_height * ROW_GAP_RATIO)

    chats = []
    current_row = [lines[0]]

    for line in lines[1:]:
        previous = current_row[-1]
        gap = line["y"] - previous["y"]

        if gap <= row_gap:
            current_row.append(line)
        else:
            chats.append(current_row)
            current_row = [line]

    chats.append(current_row)

    navigation_labels = {
        "chats", "calls", "status", "updates", "communities"
    }

    results = []

    for row in chats:
        # Remove timestamps and empty text.
        row_texts = []

        for line in row:
            cleaned = remove_timestamps(line["text"])

            if cleaned:
                row_texts.append(cleaned)

        if not row_texts:
            continue

        # Ignore navigation labels.
        if len(row_texts) == 1:
            if row_texts[0].strip().lower() in navigation_labels:
                continue

        # First line is treated as the contact name.
        # Remaining lines form the message preview.
        chat_name = row_texts[0]
        message_lines = row_texts[1:]

        last_message = (
            " ".join(message_lines)
            if message_lines
            else None
        )

        results.append({
            "chat_name": chat_name,
            "last_message": last_message
        })

    return results


def process_image(image_bytes):
    """Run OCR and convert detections directly into chat JSON."""

    ocr_result = extract_text_from_image(image_bytes)

    if not ocr_result:
        return [], ""

    detections, image_height = ocr_result

    # Preserve OCR text for debugging and frontend display.
    raw_text = "\n".join(
        item["text"]
        for item in sorted(
            detections,
            key=lambda item: (item["center_y"], item["x"])
        )
    )

    lines = group_into_lines(detections)

    chats = extract_chats_from_lines(
        lines,
        image_height
    )

    return chats, raw_text


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract-image", methods=["POST"])
def extract_image():

    if "image" not in request.files:
        return jsonify({
            "error": "Please select an image."
        }), 400

    file = request.files["image"]

    if not file or file.filename == "":
        return jsonify({
            "error": "No image selected."
        }), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": (
                "Unsupported image format. Use PNG, JPG, JPEG, "
                "BMP, TIFF, or WEBP."
            )
        }), 400

    try:
        image_bytes = file.read()

        if not image_bytes:
            return jsonify({
                "error": "The uploaded image is empty."
            }), 400

        # Validate the actual image, not just its extension.
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                image.verify()

        except (UnidentifiedImageError, OSError):
            return jsonify({
                "error": "The uploaded file is not a valid image."
            }), 400

        # OCR + Python processing; no LLM.
        chats, extracted_text = process_image(image_bytes)

        if not extracted_text.strip():
            return jsonify({
                "error": (
                    "No readable text found. "
                    "Try a clearer image."
                )
            }), 422

        result = {"chats": chats}

        # print("Extracted OCR text:")
        # print(extracted_text)

        # print("Extracted chats:")
        # print(result)

        return jsonify({
            "success": True,
            "extracted_text": extracted_text,
            "result": result
        })

    except Exception:
        app.logger.exception("Image processing failed")

        return jsonify({
            "error": "Image processing failed. Check the server logs."
        }), 500

@app.route("/download-csv", methods=["POST"])
def download_csv():
    data = request.get_json(silent=True) or {}
    chats = data.get("chats", [])

    if not isinstance(chats, list):
        return jsonify({"error": "Invalid chat data."}), 400

    output = io.StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=["chat_name", "last_message"]
    )

    writer.writeheader()

    for chat in chats:
        if not isinstance(chat, dict):
            continue

        writer.writerow({
            "chat_name": chat.get("chat_name") or "",
            "last_message": chat.get("last_message") or ""
        })

    # UTF-8 BOM helps Excel display text correctly.
    csv_content = "\ufeff" + output.getvalue()

    return Response(
        csv_content,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition":
                'attachment; filename="whatsapp_chats.csv"'
        }
    )

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "Image size exceeds the 10 MB limit."
    }), 413


if __name__ == "__main__":
    app.run(
        debug=False,
        host="127.0.0.1",
        port=5000
    )