from fastapi import FastAPI, Depends, HTTPException, status, Form, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
import os
import bcrypt

import yaml
from src.cloudflare import CF
from src.hetzner import Hetzner
from src import database

config = {}
with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.loader.SafeLoader)

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResponseModel(BaseModel):
    message: str

# Serve the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory session store
user_sessions = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(username: str, password: str):
    if username == config['webapp']['username'] and verify_password(password, config['webapp']['password']):
        return username
    return None

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = user_sessions.get(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.get("/", response_class=HTMLResponse)
async def read_index(current_user: dict = Depends(get_current_user)):
    with open(os.path.join("static", "index.html")) as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open(os.path.join("static", "login.html")) as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user = authenticate_user(username, password)
    if not user:
        return RedirectResponse(url="/login?error=invalid_credentials", status_code=status.HTTP_302_FOUND)
    # Using a simple token for demo purposes
    token = username
    user_sessions[token] = user
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.post("/change_ip", response_model=ResponseModel)
async def change_ip(current_user: dict = Depends(get_current_user)):
    try:
        hetzner = Hetzner(token=config['hetzner']['token'], 
                        server_name=config['hetzner']['server_name'],
                        used_ips=database.get_parameter('used_ips'))
        cf = CF(token=config['cloudflare']['token'], 
                zone_name=config['cloudflare']['zone_name'], 
                dns_name_proxied=config['cloudflare']['dns_name_proxied'],
                dns_name_not_proxied=config['cloudflare']['dns_name_not_proxied'])
        hetzner.delete_unused_ips()
        new_ip = hetzner.change_ip()
        database.set_parameter('used_ips', hetzner._already_used_ips)
        cf.update_record(ip = new_ip)
        result = ""
        result += f"Successfully changed the ip to {new_ip}\n"
        result += f"used_ips: {database.get_parameter('used_ips')}"
    except Exception:
        database.reset_parameters()        
        result = f"used_ips: {database.get_parameter('used_ips')}"
    return ResponseModel(message=result)

@app.post("/reset_ips", response_model=ResponseModel)
async def reset_ips(current_user: dict = Depends(get_current_user)):
    database.reset_parameters()
    result = f"used_ips: {database.get_parameter('used_ips')}"
    return ResponseModel(message=result)
