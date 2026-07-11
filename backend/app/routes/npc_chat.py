from fastapi import APIRouter
from app.models.schemas import NpcChatRequest, NpcChatResponse
from app.services import npc_chat_service

router = APIRouter()

@router.post("/npc-chat", response_model=NpcChatResponse)
def npc_chat(req: NpcChatRequest):
    return npc_chat_service.reply(req)
