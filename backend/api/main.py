from fastapi import FastAPI

app = FastAPI(title="Text Morph AI - Railway")

@app.get("/")
def read_root():
    return {"message": "Text Morph AI is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "text-morph-ai"}

# Simple text processing endpoint
@app.post("/process")
def process_text(text_input: dict):
    text = text_input.get("text", "")
    # Simple text processing without heavy AI libraries
    return {
        "original": text,
        "processed": f"Processed: {text}",
        "length": len(text),
        "words": len(text.split())
    }