import spacy
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
from pydantic import BaseModel
from typing import List
import os
import shutil
import datetime

app = FastAPI()
nlp = spacy.load("en_core_web_sm")  # Load NLP model

class SkillRequest(BaseModel):
    skill: List[str]

stored_skills = set()  # Store unique skills

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
        selected_path = "selected_resume"
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

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    contents = await file.read()

    save_path = "upload_resume"
    os.makedirs(save_path, exist_ok=True)  
    file_path = os.path.join(save_path, file.filename)

    # Save the uploaded file
    with open(file_path, "wb") as f:
        f.write(contents)

    # Extract text based on file type
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(contents)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(contents)
    else:
        return JSONResponse(content={"error": "Unsupported file format. Upload a PDF or DOCX."}, status_code=400)

    print(text)  # Debugging: prints extracted text from the resume

    analysis = analyze_resume(text, file_path)  
    return JSONResponse(content={"filename": file.filename, "analysis": analysis}, status_code=200)

@app.post("/admin")
async def admin(skill: SkillRequest): 
    global stored_skills
    stored_skills = set(skill.skill)
    print(f"Updated skills: {stored_skills}")  # Debugging
    return {"updated_skills": list(stored_skills)}

@app.get("/healthcheck")
async def healthcheck():
    return JSONResponse(content={"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()})
