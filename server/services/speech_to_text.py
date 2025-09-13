import os
import tempfile
import openai
from fastapi import UploadFile, HTTPException

def transcribe(audio_file: UploadFile) -> str:
    """
    Transcribe audio file using OpenAI Whisper API
    
    Args:
        audio_file: UploadFile containing audio data
        
    Returns:
        str: Transcribed text
    """
    try:
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY environment variable not set"
            )
        
        # Set up OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            # Read and write the uploaded file content
            content = audio_file.file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
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
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise e
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

if __name__ == "__main__":
    import os
    import traceback
    
    print("=== Whisper Speech-to-Text Test ===")
    
    # Check required environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    
    print(f"🔍 OPENAI_API_KEY: {'SET' if api_key else 'NOT SET'}")
    
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY=your-api-key")
        exit(1)
    
    print("✅ Environment variables set correctly")
    
    # Test with example file
    example_file = "./services/example_audio.wav"
    print(f"\n🔍 Looking for: {example_file}")
    
    if os.path.exists(example_file):
        file_size = os.path.getsize(example_file)
        print(f"✅ Audio file found (size: {file_size} bytes)")
        
        try:
            print("🔄 Starting transcription...")
            with open(example_file, "rb") as f:
                upload_file = UploadFile(filename="example_audio.wav", file=f)
                result = transcribe(upload_file)
                
                if result:
                    print(f"✅ Transcription successful!")
                    print(f"📝 Result: {result}")
                else:
                    print("⚠️ Transcription returned empty result")
                    
        except Exception as e:
            print(f"❌ Error during transcription:")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            print(f"   Full traceback:")
            traceback.print_exc()
    else:
        print(f"❌ Example file not found: {example_file}")
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"📂 Files in current directory: {os.listdir('.')}")
        if os.path.exists("./services"):
            print(f"📂 Files in services directory: {os.listdir('./services')}")
    
    print("\n=== Test Complete ===")