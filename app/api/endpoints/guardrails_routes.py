from fastapi import APIRouter, WebSocket, File, UploadFile
from ...services.database import SessionLocal
from ...services.guardrails_services.guardrails import Guardrails
from ...services.guardrails_services.upload_file import UploadUserFile
from ...schemas.file_schema import FileResponse
import os

router = APIRouter()

@router.websocket("/ws/guardrails")
async def guardrails_endpoint(websocket: WebSocket):
    async with SessionLocal() as db:
        Guardrails_instance = await Guardrails.create(db, user_settings={
            "assistant_id": websocket.query_params.get('assistant_id'), 
            "thread_id": websocket.query_params.get('thread_id'),
            "instruction":  websocket.query_params.get('instruction'),
            }) 
    await websocket.accept()
    while True:
        # Process user message
        data = await websocket.receive_json()
        async for response in Guardrails_instance.guardrails(data):
            await websocket.send_json(response)

# Upload file
@router.post("/uploadfile", response_model=FileResponse)
async def upload_file_endpoint(file: UploadFile = File(...)):
    UploadUserFile_Instance = await UploadUserFile.create()
    return await UploadUserFile_Instance.upload_user_file(file)