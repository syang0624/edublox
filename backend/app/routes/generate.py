from fastapi import APIRouter, HTTPException
from app.models.schemas import GenerateRequest, GenerateResponse
from app.services import storage, plan_generator, everos_memory

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        text = storage.get_upload(req.upload_id)
    except KeyError:
        raise HTTPException(404, "upload_id not found")
    try:
        recalled = everos_memory.recall_many(
            req.learner_id, everos_memory.LEARNER_RECALL_QUERIES
        )
        plan = plan_generator.generate_plan(text, recalled)
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e}")
    storage.save_plan(plan, req.learner_id)
    # recalled_memory powers the "what the tutor remembers" reveal in the
    # web app — it is exactly what the generator was shown, nothing more.
    return GenerateResponse(
        plan_id=plan.plan_id, plan=plan, recalled_memory=recalled
    )
