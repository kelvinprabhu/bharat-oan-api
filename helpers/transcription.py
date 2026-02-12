import os
import base64
import httpx
import json
import logging
from dotenv import load_dotenv
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    retry_if_exception,
    retry_if_result
)
from typing import Dict
from langcodes import Language
from openai import OpenAI
from io import BytesIO

load_dotenv()

logger = logging.getLogger(__name__)

_bhashini_client = None

def get_bhashini_client():
    global _bhashini_client
    if _bhashini_client is None:
        _bhashini_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=30.0,
                read=120.0,
                write=60.0,
                pool=10.0
            ),
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10
            )
        )
    return _bhashini_client


def base64_to_audio_file(base64_string: str, filename: str = "audio.wav") -> BytesIO:
    audio_bytes = base64.b64decode(base64_string)
    audio_file = BytesIO(audio_bytes)
    audio_file.name = filename
    return audio_file


def convert_audio_to_base64(filepath: str) -> str:
    with open(filepath, "rb") as audio_file:
        encoded_string = base64.b64encode(audio_file.read()).decode('utf-8')
    return encoded_string


def transcribe_whisper(audio_base64: str):
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    response = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=base64_to_audio_file(audio_base64),
        response_format="verbose_json"
    )
    lang_code = Language.find(response.language).language
    text = response.text
    return lang_code, text


# Custom exception for Bhashini errors
class BhashiniAPIError(Exception):
    def __init__(self, status_code, message, response_body=None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"Bhashini API Error {status_code}: {message}")


def is_retryable_status(exception):
    """Check if we should retry based on status code"""
    if isinstance(exception, BhashiniAPIError):
        # Retry on 500, 502, 503, 504, 429
        return exception.status_code in [500, 502, 503, 504, 429]
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type((
        httpx.ConnectTimeout, 
        httpx.ReadTimeout, 
        httpx.ConnectError,
        httpx.RemoteProtocolError
    )) | retry_if_exception(is_retryable_status),
    before_sleep=lambda retry_state: logger.warning(
        f"Bhashini transcribe retry {retry_state.attempt_number}: {retry_state.outcome.exception()}"
    )
)
def transcribe_bhashini(audio_base64: str, source_lang: str):
    url = 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline'
    headers = {
        'Accept': '*/*',
        'User-Agent': 'Thunder Client (https://www.thunderclient.com)',
        'Authorization': os.getenv('MEITY_API_KEY_VALUE'),
        'Content-Type': 'application/json'
    }

    if source_lang == 'en':
        service_id = "ai4bharat/whisper-medium-en--gpu--t4"  # Alternative English service
    else:
        # service_id = "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
        service_id = "bhashini/ai4bharat/conformer-multilingual-asr"

    data = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "serviceId": service_id,
                    "language": {
                        "sourceLanguage": source_lang,
                    },
                    "audioFormat": "wav",
                    "samplingRate": 16000,
                    "preProcessors": ["vad"],
                }
            }
        ],
        "inputData": {
            "audio": [
                {
                    "audioContent": audio_base64
                }
            ]
        }
    }
    
    client = get_bhashini_client()
    
    try:
        response = client.post(url, headers=headers, content=json.dumps(data))
        
        # Log response for debugging
        if response.status_code != 200:
            logger.error(f"Bhashini API returned {response.status_code}: {response.text}")
            raise BhashiniAPIError(
                status_code=response.status_code,
                message=response.text,
                response_body=response.text
            )
        
        response_json = response.json()
        return response_json['pipelineResponse'][0]['output'][0]['source']
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Status Error: {e.response.status_code} - {e.response.text}")
        raise BhashiniAPIError(
            status_code=e.response.status_code,
            message=str(e),
            response_body=e.response.text
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=20),
    retry=retry_if_exception_type((
        httpx.ConnectTimeout, 
        httpx.ReadTimeout, 
        httpx.ConnectError,
        httpx.RemoteProtocolError
    )) | retry_if_exception(is_retryable_status),
    before_sleep=lambda retry_state: logger.warning(
        f"Bhashini lang-detect retry {retry_state.attempt_number}: {retry_state.outcome.exception()}"
    )
)
def detect_audio_language_bhashini(audio_base64: str):
    url = 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline'
    headers = {
        'Accept': '*/*',
        'Authorization': os.getenv('MEITY_API_KEY_VALUE'),
        'Content-Type': 'application/json'
    }
    data = {
        "pipelineTasks": [
            {
                "taskType": "audio-lang-detection",
                "config": {
                    "language": {
                        "sourceLanguage": "auto"
                    },
                    "audioFormat": "wav",
                }
            }
        ],
        "inputData": {
            "audio": [{"audioContent": audio_base64}]
        }
    }

    client = get_bhashini_client()
    
    try:
        response = client.post(url, headers=headers, content=json.dumps(data))
        
        if response.status_code != 200:
            logger.error(f"Bhashini API returned {response.status_code}: {response.text}")
            raise BhashiniAPIError(
                status_code=response.status_code,
                message=response.text,
                response_body=response.text
            )
        
        response_json = response.json()
        detected_language_code = response_json['pipelineResponse'][0]['output'][0]['langPrediction'][0]['langCode']
        return 'en' if detected_language_code == 'en' else 'hi'
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Status Error: {e.response.status_code} - {e.response.text}")
        raise BhashiniAPIError(
            status_code=e.response.status_code,
            message=str(e),
            response_body=e.response.text
        )