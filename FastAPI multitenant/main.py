from fastapi import FastAPI, Depends, Header, HTTPException

app = FastAPI()

TENANT_DATA = {
    "acme": [{"item": "A"}, {"item": "B"}],
    "globex": [{"item": "X"}, {"item": "Y"}]
}

def get_tenant(x_tenant: str = Header(...)):
    if x_tenant not in TENANT_DATA:
        raise HTTPException(404, "Tenant not found")
    return x_tenant

@app.get("/items/")
def list_items(tenant_id: str = Depends(get_tenant)):
    return TENANT_DATA[tenant_id]

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