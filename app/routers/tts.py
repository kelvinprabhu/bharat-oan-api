from fastapi import APIRouter, Body, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from app.models.requests import TTSRequest
from helpers.tts import text_to_speech_bhashini
import uuid
import base64
import time
from helpers.utils import get_logger
from app.auth.jwt_auth import get_current_user
from helpers.telemetry import create_tts_event, TelemetryRequest
from app.tasks.telemetry import send_telemetry

logger = get_logger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post("/")
async def tts(
    request: TTSRequest = Body(...), 
    current_user: str = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Convert text to speech using the specified service."""
    session_id = request.session_id or str(uuid.uuid4())
    
    if request.service_type != 'bhashini':
        return JSONResponse({
            'status': 'error',
            'message': f'Service type "{request.service_type}" not supported. Available options: bhashini'
        }, status_code=400)
    
    start_time = time.time()
    success, status_code, error_code, error_message = False, 500, None, None
    
    try:
        audio_data = base64.b64encode(text_to_speech_bhashini(
            request.text, request.target_lang, gender='female', sampling_rate=8000
        )).decode('utf-8')
        
        success, status_code = True, 200
    except Exception as e:
        error_code, error_message = type(e).__name__, str(e)
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000
        telemetry_event = create_tts_event(
            success=success,
            latency_ms=latency_ms,
            status_code=status_code,
            error_code=error_code,
            error_message=error_message,
            language=request.target_lang,
            session_id=session_id,
            text=request.text,
            qid=request.qid or f"tts_{session_id}",
            uid=current_user
        )
        telemetry_data = TelemetryRequest(events=[telemetry_event]).model_dump()
        qid = request.qid or f"tts_{session_id}"
        logger.debug(f"TTS Telemetry - Session: {session_id}, Success: {success}, Latency: {latency_ms:.2f}ms, QID: {qid}, Language: {request.target_lang}")
        logger.debug(f"TTS Telemetry payload: {telemetry_data}")
        background_tasks.add_task(send_telemetry, telemetry_data)
     
       
    return JSONResponse({
        'status': 'success',
        'audio_data': audio_data,
        'session_id': session_id
    }, status_code=200)