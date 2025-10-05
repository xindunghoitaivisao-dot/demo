from fastapi import FastAPI, APIRouter, Depends, Response, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio

from models import User, ChatMessage, DashboardMetrics, Report
from auth import process_session_id, get_current_user

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME')

# Initialize Mongo client only if env vars are present to avoid startup failures
try:
    if mongo_url and db_name:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        logger = logging.getLogger(__name__)
        logger.info("MongoDB client initialized successfully")
    else:
        client = None
        db = None
        logger = logging.getLogger(__name__)
        logger.warning("MONGO_URL/DB_NAME not set. Database features will be disabled until provided.")
except Exception as e:
    client = None
    db = None
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize MongoDB client: {e}")

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Request/Response Models
class SessionRequest(BaseModel):
    session_id: str

class AIQueryRequest(BaseModel):
    question: str

class AIQueryResponse(BaseModel):
    answer: str
    confidence: int
    timestamp: str


# ===== AUTHENTICATION ROUTES =====

@api_router.post("/auth/session")
async def create_session(request: SessionRequest, response: Response):
    """Process session_id and create authenticated session."""
    result = await process_session_id(request.session_id, db)
    
    # Set httpOnly cookie
    response.set_cookie(
        key="session_token",
        value=result["session_token"],
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7*24*60*60,  # 7 days
        path="/"
    )
    
    return result

@api_router.get("/auth/me")
async def get_me(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get current authenticated user."""
    return current_user

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response, session_token: Optional[str] = None):
    """Logout user and clear session."""
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}


# ===== DASHBOARD ROUTES =====

@api_router.get("/dashboard/metrics")
async def get_dashboard_metrics(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get dashboard KPI metrics."""
    metrics = {
        "totalRevenue": {"value": "$2.4M", "trend": 12, "change": "+$284K"},
        "activeCustomers": {"value": "1,847", "trend": 8, "change": "+142"},
        "conversionRate": {"value": "24.3%", "trend": -2, "change": "-0.5%"},
        "aiConfidence": {"value": "94.2%", "trend": 15, "change": "+12.1%"}
    }
    return metrics

@api_router.get("/dashboard/revenue")
async def get_revenue_data(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get revenue chart data."""
    data = [
        {"month": "Jul", "revenue": 1800000},
        {"month": "Aug", "revenue": 1950000},
        {"month": "Sep", "revenue": 2100000},
        {"month": "Oct", "revenue": 2250000},
        {"month": "Nov", "revenue": 2350000},
        {"month": "Dec", "revenue": 2400000}
    ]
    return data

@api_router.get("/dashboard/customer-segmentation")
async def get_customer_segmentation(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get customer segmentation data."""
    data = [
        {"segment": "Enterprise", "value": 45, "color": "#00FFD1"},
        {"segment": "SMB", "value": 35, "color": "#6FD2C0"},
        {"segment": "Startup", "value": 20, "color": "#4D4D4D"}
    ]
    return data

@api_router.get("/dashboard/regional-performance")
async def get_regional_performance(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get regional performance data."""
    data = [
        {"region": "North America", "performance": 92},
        {"region": "Europe", "performance": 87},
        {"region": "Asia Pacific", "performance": 78},
        {"region": "Latin America", "performance": 65},
        {"region": "Middle East", "performance": 71}
    ]
    return data

@api_router.get("/dashboard/ai-insights")
async def get_ai_insights(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get AI-generated insights."""
    insights = [
        {
            "type": "success",
            "icon": "TrendingUp",
            "title": "Revenue Opportunity",
            "message": "Customer segment 'Enterprise' shows 23% higher conversion on premium features. Consider targeted upsell campaign.",
            "confidence": 94
        },
        {
            "type": "warning",
            "icon": "AlertTriangle",
            "title": "Churn Risk Alert",
            "message": "12 high-value accounts showing decreased engagement patterns. Proactive outreach recommended.",
            "confidence": 87
        },
        {
            "type": "info",
            "icon": "Lightbulb",
            "title": "Market Trend",
            "message": "Industry benchmark analysis suggests expanding AI advisory services could capture $1.2M additional TAM.",
            "confidence": 82
        },
        {
            "type": "success",
            "icon": "Target",
            "title": "Optimization Win",
            "message": "Recent model update improved prediction accuracy by 8.3%, reducing false positives by 34%.",
            "confidence": 96
        }
    ]
    return insights


# ===== REPORTS ROUTES =====

@api_router.get("/reports")
async def get_reports(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get all reports."""
    reports = await db.reports.find({"user_id": current_user.id}).to_list(100)
    
    # If no reports exist, return mock data
    if not reports:
        mock_reports = [
            {"id": "1", "name": "Q4 Performance Analysis", "date": "2025-01-15", "type": "Financial", "status": "Ready"},
            {"id": "2", "name": "Customer Behavior Insights", "date": "2025-01-14", "type": "Marketing", "status": "Ready"},
            {"id": "3", "name": "AI Model Performance Review", "date": "2025-01-13", "type": "Technical", "status": "Ready"},
            {"id": "4", "name": "Market Expansion Forecast", "date": "2025-01-12", "type": "Strategy", "status": "Processing"},
            {"id": "5", "name": "Competitive Analysis", "date": "2025-01-10", "type": "Research", "status": "Ready"}
        ]
        return mock_reports
    
    return reports

@api_router.get("/report-categories")
async def get_report_categories(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get report categories."""
    categories = [
        {"title": "Monthly Performance", "description": "Comprehensive overview of business metrics and KPIs", "type": "Financial", "lastGenerated": "2025-01-15"},
        {"title": "Customer Analysis", "description": "Deep dive into customer behavior and segmentation", "type": "Marketing", "lastGenerated": "2025-01-14"},
        {"title": "Predictive Forecast", "description": "AI-powered projections for next quarter", "type": "Strategy", "lastGenerated": "2025-01-12"},
        {"title": "Market Trends", "description": "Industry analysis and competitive positioning", "type": "Research", "lastGenerated": "2025-01-11"},
        {"title": "Operational Efficiency", "description": "Process optimization opportunities", "type": "Operations", "lastGenerated": "2025-01-10"},
        {"title": "Risk Assessment", "description": "Potential threats and mitigation strategies", "type": "Compliance", "lastGenerated": "2025-01-09"}
    ]
    return categories


# ===== AI INSIGHTS CHAT ROUTES =====

@api_router.post("/ai/chat", response_model=AIQueryResponse)
async def ai_chat(request: Request, query: AIQueryRequest, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Chat with AI about business data."""
    try:
        # Get API key
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Initialize LLM chat
        chat = LlmChat(
            api_key=api_key,
            session_id=f"user_{current_user.id}",
            system_message="You are an AI business analyst assistant for VinaEu AI. Analyze data and provide actionable insights about business performance, customer behavior, and strategic opportunities. Be concise and data-driven."
        )
        
        # Use gpt-4o model
        chat.with_model("openai", "gpt-4o")
        
        # Create user message
        user_message = UserMessage(text=query.question)
        
        # Get AI response
        response = await chat.send_message(user_message)
        
        # Save to database
        chat_message = ChatMessage(
            user_id=current_user.id,
            role="user",
            content=query.question
        )
        await db.chat_messages.insert_one(chat_message.dict())
        
        ai_message = ChatMessage(
            user_id=current_user.id,
            role="assistant",
            content=response,
            confidence=92
        )
        await db.chat_messages.insert_one(ai_message.dict())
        
        return AIQueryResponse(
            answer=response,
            confidence=92,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        return AIQueryResponse(
            answer="I apologize, but I encountered an error processing your question. Please try again.",
            confidence=0,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

@api_router.get("/ai/history")
async def get_ai_history(request: Request, current_user: User = Depends(lambda req: get_current_user(req, db))):
    """Get AI chat history."""
    messages = await db.chat_messages.find({"user_id": current_user.id}).sort("timestamp", -1).limit(50).to_list(50)
    
    # Group messages into conversations
    conversations = []
    for i in range(0, len(messages), 2):
        if i + 1 < len(messages) and messages[i]["role"] == "assistant" and messages[i+1]["role"] == "user":
            conversations.append({
                "id": str(i // 2 + 1),
                "question": messages[i+1]["content"],
                "answer": messages[i]["content"],
                "confidence": messages[i].get("confidence", 90),
                "timestamp": messages[i]["timestamp"].strftime("%Y-%m-%d %H:%M")
            })
    
    # If no history, return mock data
    if not conversations:
        conversations = [
            {
                "id": "1",
                "question": "What's driving the recent revenue increase?",
                "answer": "Analysis shows three primary drivers: 1) 23% increase in enterprise customer acquisition, 2) 15% improvement in customer retention through AI-powered engagement, and 3) successful launch of premium AI advisory services contributing $340K additional revenue.",
                "confidence": 92,
                "timestamp": "2025-01-15 14:30"
            }
        ]
    
    return conversations


# Health check
@api_router.get("/")
async def root():
    return {"message": "VinaEu AI API v1.0", "status": "healthy"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        if client:
            client.close()
    except Exception:
        pass
