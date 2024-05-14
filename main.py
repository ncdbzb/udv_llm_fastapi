import uvicorn
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.cors import CORSMiddleware

from src.auth.auth_config import auth_backend, fastapi_users
from src.auth.schemas import UserRead, UserCreate, UserUpdate
from src.auth.routers.verify_router import router as verify_router
from src.auth.routers.forgot_pass_router import router as forgot_pass_router
from src.docs.router import router as upload_docs_router
from src.llm_service.router import router as llm_service_router
from src.admin_panel.router import router as admin_panel_router
from config.config import CORS_ORIGINS


app = FastAPI(
    title="UDV LLM",
    root_path="/api"
)

# app.add_middleware(HTTPSRedirectMiddleware)

# headers = ["Content-Type", "Set-Cookie", "Access-Control-Allow-Headers", "Access-Control-Allow-Origin",
#            "Authorization", "Cookie", "Accept"]
# methods = ["GET", "POST", "OPTIONS", "DELETE", "PATCH", "PUT"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=True),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(
    verify_router,
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    forgot_pass_router,
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    upload_docs_router,
    prefix="/docks",
    tags=["Docs"],
)
app.include_router(
    llm_service_router
)
app.include_router(
    admin_panel_router,
    prefix="/admin",
    tags=["Admin"]
)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        # ssl_keyfile='/chatops_udv/fast_api/certs/key.pem',
        # ssl_certfile='/chatops_udv/fast_api/certs/cert.pem'
    )
