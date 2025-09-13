import openai
from fastapi import UploadFile, HTTPException
import tempfile
import os

# Set up OpenAI client with API key from environment
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def transcribe(audio_file: UploadFile) -> str:
    """
    Transcribe audio file using OpenAI Whisper API
    
    Args:
        audio_file: UploadFile containing audio data
        
    Returns:
        str: Transcribed text
    """
    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_file:
            # Read and write the uploaded file content
            content = audio_file.file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Open the temporary file for Whisper API
        with open(temp_file_path, "rb") as audio:
            # Call OpenAI Whisper API
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        # Reset file pointer for potential future use
        audio_file.file.seek(0)
        
        return transcript
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        raise HTTPException(
            status_code=500,
            detail=f"Error transcribing audio: {str(e)}"
        )
    
if __name__ == "__main__":
    # Example usage
    with open("example_audio.mp3", "rb") as f:
        upload_file = UploadFile(filename="example_audio.mp3", file=f)
        transcription = transcribe(upload_file)
        print("Transcription:", transcription)