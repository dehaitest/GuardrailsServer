# app/api/v1/api.py
from fastapi import APIRouter
from .endpoints import guardrails_routes, prompt_routes

api_router = APIRouter()
api_router.include_router(guardrails_routes.router, tags=["guardrails"])
api_router.include_router(prompt_routes.router, tags=["prompt"])

