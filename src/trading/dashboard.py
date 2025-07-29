from fastapi import FastAPI, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .state import StateStore

app = FastAPI()
security = HTTPBasic()
state = StateStore()


def auth(credentials: HTTPBasicCredentials = Depends(security)):
    # very simple auth check
    if credentials.username != "admin" or credentials.password != "admin":
        raise Exception("auth failed")
    return True


@app.get("/pnl")
def pnl(_: bool = Depends(auth)):
    return state.load_pnl()


@app.get("/agents")
def agents(_: bool = Depends(auth)):
    weights = state.load_weights()
    return weights
