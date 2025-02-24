import spacy
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse,FileResponse
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
from pydantic import BaseModel
from typing import List
import os
import shutil
import datetime
import uvicorn

app = FastAPI()
nlp = spacy.load("en_core_web_sm")  # Load NLP model


selected_path = "selected_resume"
os.makedirs(selected_path, exist_ok=True) 

upload_folder = "upload_resume"
os.makedirs(upload_folder, exist_ok=True) 

class SkillRequest(BaseModel):
    skill: List[str]

stored_skills = set() 




# Function to extract text from PDF
def extract_text_from_pdf(pdf_bytes):
    reader = PdfReader(BytesIO(pdf_bytes))
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

# Function to extract text from DOCX
def extract_text_from_docx(docx_bytes):
    doc = Document(BytesIO(docx_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

# Function to analyze resume content
def analyze_resume(text, file_path):
    doc = nlp(text)
    found_skills = [token.text for token in doc if token.text in stored_skills]

    if found_skills:  # If any matching skill is found
        os.makedirs(selected_path, exist_ok=True)

        selected_file_path = os.path.join(selected_path, os.path.basename(file_path))

        # Move the original file, handle if file exists
        try:
            shutil.move(file_path, selected_file_path)
            print(f"Resume stored in: {selected_file_path}")
        except Exception as e:
            print(f"Error moving file: {e}")

    return {
        "word_count": len(text.split()),
        "found_skills": list(set(found_skills)),
        "suggestions": "Consider adding more technical skills or certifications."
    }


@app.get("/getAllSelected")
async def get_all_selected_files():
    try:
 
        if not os.path.exists(selected_path):
            return JSONResponse(content={"error": "Selected resumes directory does not exist."}, status_code=404)

       
        selected_files = os.listdir(selected_path)
        
        if not selected_files:
            return JSONResponse(content={"message": "No selected resumes found."}, status_code=200)

        return JSONResponse(content={"selected_files": selected_files}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/upload")
async def upload_resume(files: list[UploadFile] = File(...)):
     uploaded_files_info = []

     for file in files:
        contents = await file.read()
        file_path = os.path.join(upload_folder, file.filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)

        # Extract text based on file type
        if file.filename.endswith(".pdf"):
            text = extract_text_from_pdf(contents)
        elif file.filename.endswith(".docx"):
            text = extract_text_from_docx(contents)
        else:
            return JSONResponse(content={"error": f"Unsupported file format: {file.filename}. Upload a PDF or DOCX."}, status_code=400)

        # Analyze the resume
        analysis = analyze_resume(text, file_path)

        uploaded_files_info.append({
            "filename": file.filename,
            "analysis": analysis
        })

     return JSONResponse(content={"uploaded_files": uploaded_files_info}, status_code=200)

@app.post("/admin")
async def admin(skill: SkillRequest): 
    global stored_skills
    stored_skills = set(skill.skill)
    print(f"Updated skills: {stored_skills}")  # Debugging
    return {"updated_skills": list(stored_skills)}


@app.get("/download/{filename}")
async def download_resume(filename: str):
    file_path = os.path.join(selected_path, filename)
    print("download called")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/octet-stream", filename=filename)
    return JSONResponse(content={"error": "File not found"}, status_code=404)

@app.get("/healthcheck")
async def healthcheck():
    return JSONResponse(content={"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()})


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)