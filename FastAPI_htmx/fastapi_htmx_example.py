from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def serve_form():
    return """
    <form
      hx-post="/add-item"
      hx-target="#form-error"
      hx-swap="innerHTML"
      hx-on="error: alert('Something went wrong')"
    >
      <input name="item" />
      <button type="submit">Add</button>
    </form>

    <div id="form-error"></div>
    """

@app.post("/add-item", response_class=HTMLResponse)
async def add_item(item: str = Form(...)):
    print (f"Received item: {item}")
    if not item:
        raise HTTPException(status_code=400, detail="Item cannot be empty")
    return f"<p>Item '{item}' added successfully!</p>"