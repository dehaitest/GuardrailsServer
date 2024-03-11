from fastapi import APIRouter, WebSocket, File, Depends, UploadFile
from ...services.database import SessionLocal
from ...services.guardrails_services.guardrails import Guardrails
from ...services.guardrails_services.upload_file import UploadUserFile
from ...schemas.file_schema import FileResponse
from ..dependencies import get_current_user
from ...services.user_service import validate_token 

router = APIRouter()

@router.websocket("/ws/guardrails")
async def guardrails_endpoint(websocket: WebSocket):
    async with SessionLocal() as db:
        valid_user = await validate_token(db, websocket.query_params.get('token', ""))
        if not valid_user:
            await websocket.close(code=1008)  
            return  
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
async def upload_file_endpoint(file: UploadFile = File(...), user_uuid = Depends(get_current_user)):
    UploadUserFile_Instance = await UploadUserFile.create()
    return await UploadUserFile_Instance.upload_user_file(file)