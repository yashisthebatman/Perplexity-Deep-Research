# schemas.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional,Union

class ResearchRequest(BaseModel):
    topic: str

class ReportSection(BaseModel):
    title: str
    content: str
    sources: Optional[List[str]] = None

class ChartDataset(BaseModel):
    label: str
    data: List[Union[int, float]] # Data points for the chart
    # Add other Chart.js specific dataset properties if needed, e.g., backgroundColor

class ChartData(BaseModel):
    type: str # e.g., 'bar', 'line', 'pie'
    labels: List[str] # Labels for the x-axis or pie slices
    datasets: List[ChartDataset]
    title: Optional[str] = None

class ReportResponse(BaseModel):
    report_id: str
    topic: str
    summary: Optional[ReportSection] = None
    medical_data_analysis: Optional[ReportSection] = None
    trends_analysis: Optional[ReportSection] = None
    government_schemes: Optional[ReportSection] = None
    diseases_on_rise: Optional[ReportSection] = None
    charts: Optional[List[ChartData]] = []
    full_text_for_follow_up: str

class QuestionRequest(BaseModel):
    report_id: str
    question: str
    report_context: str

class AnswerResponse(BaseModel):
    answer: str
    sources: Optional[List[str]] = None

# Added for type hint in ChartDataset