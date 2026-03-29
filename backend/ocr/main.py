from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
import pytesseract
import uvicorn


app = FastAPI()


@app.post(
    "/ocr",
    summary="Extract text from an uploaded image",
    response_description="Recognized OCR text",
)
async def ocr(image: UploadFile = File(..., description="Image file to process")) -> dict[str, str]:
    try:
        if image.content_type and not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image uploads are supported.")

        content = await image.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with Image.open(BytesIO(content)) as pil_image:
            # Normalize mode for more consistent OCR behavior across formats.
            text = pytesseract.image_to_string(pil_image.convert("RGB"), lang="eng+hin")

        return {"text": text}
    except HTTPException:
        raise
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await image.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
