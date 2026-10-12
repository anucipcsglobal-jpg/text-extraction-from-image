# Smart Image Data Extractor

A web-based image text extraction application built using Python, Flask, RapidOCR, and Pillow. The application extracts text from uploaded images, organizes detected text into structured JSON, and allows users to download chat data as a CSV file.

## Features

- Upload images using file selection or drag and drop.
- Preview images before processing.
- Extract text from images using RapidOCR.
- Organize detected text into chat names and message previews.
- Display extracted data in JSON format.
- Copy JSON results to the clipboard.
- Download extracted chat data as a CSV file.
- Validate image formats and uploaded file contents.
- Support image uploads up to 10 MB.
- Process images locally without requiring Ollama or an LLM.

## Technologies Used

- **Python** - Backend processing.
- **Flask** - Web framework and API endpoints.
- **RapidOCR** - Optical character recognition.
- **Pillow** - Image loading and preprocessing.
- **HTML** - Frontend structure.
- **CSS** - User interface styling.
- **JavaScript** - Upload handling, API requests, and downloads.
- **CSV** - Export extracted data.

## Project Structure

```text
smart-image-data-extractor/
├── app.py
├── templates/
│   └── index.html
├── requirements.txt
├── README.md
└── .gitignore
```

## Requirements

- Python 3.10 or a compatible version supported by your RapidOCR dependencies.
- pip package manager.
- Internet connection for installing dependencies.

Ollama and Tesseract are not required.

## Installation

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd smart-image-data-extractor
```

Replace `<YOUR_REPOSITORY_URL>` with your repository URL.

### 2. Create a Virtual Environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux or macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

Create a `requirements.txt` file:

```text
Flask
Pillow
rapidocr
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Depending on your RapidOCR version, an additional inference backend may be required. Install a compatible backend according to the RapidOCR documentation if necessary.

### 4. Run the Application

```bash
python app.py
```

Open the following URL in your browser:

http://127.0.0.1:5000

## How to Use

1. Start the Flask application.
2. Open the application in your browser.
3. Upload an image using the file picker or drag-and-drop area.
4. Preview the selected image.
5. Click **Extract Image Data**.
6. View the extracted JSON and OCR text.
7. Click **Copy JSON** to copy the JSON output.
8. Click **Download CSV** to download the extracted chat records.

## Supported Image Formats

- PNG
- JPG
- JPEG
- WEBP
- BMP
- TIFF

**Maximum file size:** 10 MB.

## Output Format

### JSON Output

The extracted data is returned in the following format:

```json
{
  "chats": [
    {
      "chat_name": "David Warner",
      "last_message": "Video"
    },
    {
      "chat_name": "Rock",
      "last_message": "Hey! When is the meeting today?"
    },
    {
      "chat_name": "Alena",
      "last_message": "Hey! Will you join the meeting?"
    }
  ]
}
```

The example is illustrative. Actual results depend on the uploaded image and OCR accuracy.

### CSV Output

The application generates a file named `whatsapp_chats.csv`.

Example:

```csv
chat_name,last_message
David Warner,Video
Rock,Hey! When is the meeting today?
Alena,Hey! Will you join the meeting?
```

The CSV contains two columns:

- `chat_name` - Detected contact or chat name.
- `last_message` - Detected message preview.

## API Endpoints

### 1. Home Page

**Endpoint:** `GET /`

Renders the application interface.

### 2. Extract Image

**Endpoint:** `POST /extract-image`

Accepts an image using multipart form data.

Example:

```bash
curl -X POST \
  -F "image=@screenshot.png" \
  http://127.0.0.1:5000/extract-image
```

Returns extracted OCR text and structured JSON.

### 3. Download CSV

**Endpoint:** `POST /download-csv`

Accepts extracted chat data as JSON and returns a downloadable CSV file.

Example request:

```json
{
  "chats": [
    {
      "chat_name": "David Warner",
      "last_message": "Video"
    },
    {
      "chat_name": "Rock",
      "last_message": "Hello"
    }
  ]
}
```

Example command:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"chats":[{"chat_name":"David Warner","last_message":"Video"}]}' \
  -o whatsapp_chats.csv \
  http://127.0.0.1:5000/download-csv
```

## How It Works

1. Flask receives the uploaded image.
2. Pillow validates the image and corrects its orientation.
3. RapidOCR detects text and its bounding boxes.
4. Python groups text detections according to their positions.
5. The extracted text is organized into chat names and message previews.
6. Flask returns the results as JSON.
7. The CSV endpoint converts chat records into a downloadable CSV file.

## Configuration

### Maximum Upload Size

The default upload limit is configured in `app.py`:

```python
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
```

### OCR Image Dimensions

Images are resized before OCR processing to help control memory usage:

```python
image.thumbnail((1800, 1800))
```

### Chat Row Grouping

The grouping threshold can be adjusted to suit different screenshot layouts:

```python
ROW_GAP_RATIO = 0.022
```

The appropriate value depends on image dimensions, text spacing, and chat row heights.

## Error Handling

The application handles common errors, including:

- Missing image uploads.
- Unsupported image formats.
- Invalid or corrupted images.
- Empty uploads.
- Files exceeding the upload limit.
- Images containing no readable text.
- OCR processing failures.
- Invalid CSV requests.

## Limitations

- OCR accuracy depends on image quality, resolution, and text clarity.
- Chat grouping relies on bounding-box positions and predefined rules.
- Wrapped message previews may be assigned incorrectly.
- Unusual layouts can cause adjacent chat entries to merge or split.
- OCR may misread names, numbers, timestamps, and attachment labels.
- Results should be checked against the original screenshot when accuracy is important.

## Privacy

The application can run locally on your computer. This implementation uses RapidOCR and Python processing without sending image contents to an LLM service.

The application does not intentionally save uploaded images to disk. If deployed remotely, uploaded images are transmitted to the server hosting the application.

## Troubleshooting

### Application Does Not Start

Ensure your virtual environment is activated and dependencies are installed:

```bash
pip install -r requirements.txt
```

### RapidOCR Initialization Fails

Check your Python version and install the inference backend compatible with your RapidOCR release.

### Incorrect Chat Grouping

Inspect the extracted OCR text and adjust the grouping threshold or row-grouping logic.

### CSV Download Fails

Ensure that the Flask application contains the `/download-csv` route and that the frontend sends a valid JSON request containing a `chats` array.

## Future Improvements

- Improved chat row detection.
- Support for multiple images.
- Excel export (`.xlsx`).
- Better timestamp removal.
- Improved handling of multiline message previews.
- Unit tests for OCR processing and CSV generation.
- Support for additional document types.

## License

Add a suitable license, such as the MIT License, if you plan to distribute this project publicly.

---

**Built with Python, Flask, RapidOCR, and Pillow.**