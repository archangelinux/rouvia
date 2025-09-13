import requests
import base64
import os
from fastapi import UploadFile, HTTPException

def transcribe(audio_file: UploadFile) -> str:
    """
    Transcribe MP3 audio file using Google Cloud Speech-to-Text REST API with API key
    
    Args:
        audio_file: UploadFile containing MP3 audio data
        
    Returns:
        str: Transcribed text
    """
    try:
        # Get API key from environment
        api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_CLOUD_API_KEY environment variable not set"
            )
        
        # Read and encode audio content
        audio_content = audio_file.file.read()
        encoded_audio = base64.b64encode(audio_content).decode('utf-8')
        
        # Prepare request to Google Speech-to-Text API
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
        
        # Request payload for MP3
        payload = {
            "config": {
                "encoding": "MP3",
                "languageCode": "en-US",
                "enableAutomaticPunctuation": True,
            },
            "audio": {
                "content": encoded_audio
            }
        }
        
        # Make request
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Google API error: {response.text}"
            )
        
        # Parse response and extract transcript
        result = response.json()
        transcript_parts = []
        
        if "results" in result:
            for res in result["results"]:
                if "alternatives" in res and res["alternatives"] and res["alternatives"][0].get("transcript"):
                    transcript_parts.append(res["alternatives"][0]["transcript"])
        
        # Reset file pointer
        audio_file.file.seek(0)
        
        return " ".join(transcript_parts)
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

if __name__ == "__main__":
    import os
    
    # Check API key
    if not os.getenv("GOOGLE_CLOUD_API_KEY"):
        print("❌ GOOGLE_CLOUD_API_KEY environment variable not set")
        exit(1)
    
    # Test with example file
    example_file = "./services/example_audio.mp3"
    if os.path.exists(example_file):
        with open(example_file, "rb") as f:
            upload_file = UploadFile(filename="example_audio.mp3", file=f)
            try:
                result = transcribe(upload_file)
                print(f"Transcription: {result}")
            except Exception as e:
                print(f"Error: {e}")
    else:
        print(f"Example file not found: {example_file}")