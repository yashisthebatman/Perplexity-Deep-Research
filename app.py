# app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import uvicorn
import os

from schemas import ResearchRequest, ReportResponse, QuestionRequest, AnswerResponse
from services import conduct_deep_research, answer_follow_up_question, generate_report_id

load_dotenv()

app = FastAPI(
    title="Perplexity Health Researcher",
    description="API for conducting deep health research using Perplexity AI.",
    version="0.1.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# In-memory storage for reports (for hackathon simplicity
generated_reports_cache = {} # Stores ReportResponse objects

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/research", response_model=ReportResponse)
async def create_research_report(research_request: ResearchRequest):
    topic = research_request.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    print(f"Received research request for topic: {topic}")
    
    report_id = generate_report_id(topic)
    if report_id in generated_reports_cache:
        print(f"Returning cached report for topic: {topic}, ID: {report_id}")
        return generated_reports_cache[report_id]

    try:
        # conduct_deep_research is now async, but it calls synchronous get_perplexity_response.
        # FastAPI handles running sync functions in a thread pool if called from an async path.
        # For true async, get_perplexity_response and the OpenAI client would need to be async.
        report_dict_data = await conduct_deep_research(topic)
        
        # Ensure the dictionary has all keys expected by ReportResponse, with defaults for missing optional fields
        # This is mostly handled by Pydantic itself if types are Optional
        
        response_model = ReportResponse(**report_dict_data) # Pydantic validation
        
        generated_reports_cache[response_model.report_id] = response_model
        print(f"Research complete for: {topic}. Report ID: {response_model.report_id}")
        return response_model
    except Exception as e:
        print(f"Error during research for topic '{topic}': {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to conduct research: {str(e)}")

@app.post("/ask", response_model=AnswerResponse)
async def ask_follow_up(question_request: QuestionRequest):
    report_id = question_request.report_id
    question = question_request.question.strip()
    report_context = question_request.report_context # Passed by the client

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not report_context: # Check if context is provided by client
         # Fallback: try to get from cache if client didn't send it (though client should send it)
        cached_report = generated_reports_cache.get(report_id)
        if not cached_report or not cached_report.full_text_for_follow_up:
             raise HTTPException(status_code=400, detail="Report context is missing and not found in cache.")
        report_context = cached_report.full_text_for_follow_up
        print(f"Used cached report context for report ID: {report_id}")


    print(f"Received follow-up question: '{question}' for report ID: {report_id}")

    try:
        answer_text = await answer_follow_up_question(question, report_context)
        return AnswerResponse(answer=answer_text) # Sources are not explicitly handled for follow-ups here
    except Exception as e:
        print(f"Error answering follow-up question: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get answer: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Ensure reload is True for development convenience
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)