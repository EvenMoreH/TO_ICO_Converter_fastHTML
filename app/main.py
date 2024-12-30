from fasthtml.common import * # type: ignore
from fasthtml.common import (
    Form, Input, Button, Html, Head, Body, Div, P, Title, Titled, Base, Link, Br, A, Img, Meta, UploadFile ,Response
)
from PIL import Image # type: ignore
from pathlib import Path
from starlette.responses import FileResponse
from mimetypes import guess_type
import os
import time
from datetime import datetime

# for Docker
app, rt = fast_app(static_path="static") # type: ignore

# for local
# app, rt = fast_app(static_path="app/static") # type: ignore


temp_dir = Path("app/temp")
temp_dir.mkdir(parents=True, exist_ok=True)

# using a class here so I can have a proper type assign to paths and names that is used globally
class GlobalPath:
    file_path: Path

class GlobalOutputPath:
    output_path: str

class GlobalFileName:
    file_name: str

class GlobalFileExtension:
    file_extension: str

def png_to_ico(image_path, output_path, target_size=(256, 256)):
   with Image.open(image_path) as img:
       # Crop to square if needed
       width, height = img.size
       if width != height:
           size = min(width, height)
           left = (width - size) // 2
           top = (height - size) // 2
           right = left + size
           bottom = top + size
           img = img.crop((left, top, right, bottom))

       # Resize if too large
       if width > 256 or height > 256:
           img = img.resize(target_size, Image.Resampling.LANCZOS)

       img = img.convert('RGBA')
       img.save(output_path, format='ICO', sizes=[img.size])

# removing temp files
def remove_old_files(folder, seconds):
    # Calculate the threshold time (in seconds)
    now = time.time()
    age_threshold = now - seconds  # 2 days = 2 * 86400 seconds

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)

        # Check if it's a file
        if os.path.isfile(file_path):
            # Get the file's last modified time
            file_mtime = os.path.getmtime(file_path)

            # Check if the file is older than the threshold
            if file_mtime < age_threshold:
                log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"LOG: {log_time} - Removing old file: {file_path}")
                os.remove(file_path)  # Delete the file


@rt("/")
def homepage():
    time_to_remove = 86400
    remove_old_files(temp_dir, time_to_remove)  # Removes files older than [in seconds]

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title("ICO Converter"),
            Link(rel="stylesheet", href="styles.css"),
            Link(rel="icon", href="images/favicon.ico", type="image/x-icon"),
            Link(rel="icon", href="images/favicon.png", type="image/png"),
        ),
        Body(
            Titled("Image to .ico Converter"),
            Form(
                P("Select file", cls="select"),
                Input(type="file", name="file", required=True, cls="browse"),
                Br(),
                Br(),
                Br(),
                Button("Upload and Convert", type="submit"),
                method="post",
                action="/upload",
                enctype="multipart/form-data", # required for file uploading (to be researched),
            ),
            cls="container"
        )
    )

# handles uploading file to temp location and removes it after conversion button is pressed
@rt("/upload", methods=["GET", "POST"])
async def upload(file: UploadFile = None):
    filebuffer = await file.read()  # Read file content
    GlobalPath.file_path = temp_dir / file.filename  # Define path to save file
    GlobalPath.file_path.write_bytes(filebuffer)  # Save file

    image_path = GlobalPath.file_path
    ico_extension = ".ico"
    GlobalOutputPath.output_path = os.path.join(temp_dir, image_path.stem) + ico_extension

    # conversion function call
    png_to_ico(image_path, GlobalOutputPath.output_path, target_size=(256, 256))

    GlobalFileName.file_name = GlobalPath.file_path.stem  # extracts main file name
    GlobalFileExtension.file_extension = ico_extension.lstrip('.')

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Title("ICO Converter"),
            Link(rel="stylesheet", href="styles.css"),
            Link(rel="icon", href="images/favicon.ico", type="image/x-icon"),
            Link(rel="icon", href="images/favicon.png", type="image/png"),
        ),
        Body(
            Titled("File Uploaded Successfully"),
            Div(
                P(f"File \"{file.filename}\" was uploaded successfully and converted to \"{GlobalFileName.file_name}.{GlobalFileExtension.file_extension}\""),
                Br(),
                Form(
                    Button("Go To Downloads", type="submit"),
                    method="get",
                    action=f"/page/{GlobalFileName.file_name}/{GlobalFileExtension.file_extension}",
                    cls="container"
                )
            )
        )
    )


@rt("/download/{filename}/{extension}", methods=["GET"])
async def download(filename: str, extension: str):
    # Ensure the file exists
    if not os.path.exists(GlobalOutputPath.output_path):
        return Response("File not found", status_code=404)

    # Guess MIME type
    mime_type, _ = guess_type(GlobalOutputPath.output_path)
    if not mime_type:
        mime_type = "application/octet-stream"  # Default fallback

    # Serve the file with a proper Content-Disposition header
    return FileResponse(
        GlobalOutputPath.output_path,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}.{extension}"'}
    )

@rt("/page/{filename}/{extension}", methods=["GET"])
def download_page(filename: str, extension: str):
    # Create a FastHTML page with a download link and other elements
    return Html(
            Head(
                # using base with only "/" to make the path absolute - works locally
                Base(href="/"),
                Meta(name="viewport", content="width=device-width, initial-scale=1"),
                Title("ICO Converter"),
                Link(rel="stylesheet", href="styles.css"),
                Link(rel="icon", href="images/favicon.ico", type="image/x-icon"),
                Link(rel="icon", href="images/favicon.png", type="image/png"),
            ),
            Body(
                Titled("Download Your File"),
                Div(
                    P("File Preview", style="min-width: 220px", cls="select"),
                    Br(),
                    Img(src=f"/download/{filename}/{extension}", alt="img", style="max-width: 100%; height: auto; margin: auto;"),
                    )
                ),
                Div(
                    Br(),
                ),
                Div(
                    Button(
                        A(
                        "Download Converted File",
                        href=f"/download/{filename}/{extension}",
                        ),
                    ),
                    cls="container",
                ),
                Div(
                    Br()
                ),
                Div(
                    Button(
                        A("Return to Home", href="/"),
                    ),
                    cls="container",
                ),
            )

if __name__ == '__main__':
    # Important: Use host='0.0.0.0' to make the server accessible outside the container
    serve(host='0.0.0.0', port=5003) # type: ignore