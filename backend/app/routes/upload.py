import uuid
from fastapi import APIRouter, UploadFile, HTTPException
from app.services import pdf_extractor, storage
from app.models.schemas import UploadResponse

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    contents = await file.read()
    if len(contents) > 25 * 1024 * 1024:
        raise HTTPException(400, "File exceeds 25MB")
    text = pdf_extractor.extract_text(contents)
    if len(text.strip()) < 100:
        raise HTTPException(400, "Could not extract meaningful text from PDF")
    # Truncate to keep LLM cost down
    text = text[:15000]
    upload_id = uuid.uuid4().hex
    storage.save_upload(upload_id, text)
    return UploadResponse(
        upload_id=upload_id,
        extracted_text_preview=text[:500],
        char_count=len(text),
    )
