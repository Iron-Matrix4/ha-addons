import wave
import sys
import argparse
from piper import PiperVoice

def main():
    parser = argparse.ArgumentParser(description="Piper TTS Inference")
    parser.add_argument("--model", required=True, help="Path to ONNX model")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    parser.add_argument("--output", required=True, help="Output WAV path")
    parser.add_argument("--text", required=True, help="Text to speak")
    args = parser.parse_args()

    print(f"Loading model from {args.model}...")
    try:
        voice = PiperVoice.load(args.model, args.config)
        print("Model loaded.")
        
        # Debug: Test phonemization
        # print(f"Phonemizing: '{args.text}'")
        # phonemes = voice.phonemize(args.text)
        # print(f"Phonemes: {phonemes}")
        
        # Try synthesize_wav with wave object
        print("Synthesizing...")
        with wave.open(args.output, "wb") as wav_file:
            voice.synthesize_wav(args.text, wav_file)
        
        print(f"Saved to {args.output}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
