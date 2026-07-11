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
        learner_context = everos_memory.recall(
            req.learner_id,
            "Learning preferences, recurring misconceptions, recent progress, and helpful teaching approaches",
        )
        plan = plan_generator.generate_plan(text, learner_context)
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {e}")
    storage.save_plan(plan, req.learner_id)
    return GenerateResponse(plan_id=plan.plan_id, plan=plan)
