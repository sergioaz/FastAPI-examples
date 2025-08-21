from fastapi import FastAPI, BackgroundTasks, UploadFile, File
import shutil
import os
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def clean_temp_file(file_path: str):
    if os.path.exists(file_path):
        #os.remove(file_path)
        print (f"file {file_path} was uploaded!")


@app.post("/upload")
async def handle_upload(bg_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    bg_tasks.add_task(clean_temp_file, file_path)
    return {"message": "Upload successful", "filename": file.filename}

def main():
    import uvicorn
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
