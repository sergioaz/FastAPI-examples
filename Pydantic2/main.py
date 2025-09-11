from typing import Optional

from fastapi import FastAPI, HTTPException, Query

from pydantic import BaseModel
from fastapi.responses import ORJSONResponse


app = FastAPI()

"""
🧱 Path Parameters
Still a staple. Still simple.

Use them when the resource is directly represented by the URL — like a specific product.
"""
class Product(BaseModel):
    id: int
    name: str
    price: float
    category: str

products = {
    1: Product(id=1, name="Laptop", price=999.99, category="Electronics"),
    2: Product(id=2, name="Running Shoes", price=89.99, category="Sports"),
}

@app.get("/products/{product_id}")
async def get_product(product_id: int):
    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")
    return products[product_id]

"""
🔍 Query Parameters (Now Less Verbose)
Remember using Field and thinking, “wow this feels like overkill”? That’s gone.
Old way:

class ProductRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=50, description="Product name")
    price: float = Field(..., gt=0, description="Product price")
    category: str = Field(default="General", description="Product category")

@app.post("/products/")
async def create_product(product: ProductRequest):
    return product

Pydantic 2 lets you drop Field(imported) and just pass kwargs into Query.
"""

products = {
    1: {"id": 1, "name": "Laptop", "category": "Electronics", "price": 999.99},
    2: {"id": 2, "name": "Smartphone", "category": "Electronics", "price": 699.99},
    3: {"id": 3, "name": "Coffee Maker", "category": "Home Appliances", "price": 49.99},
    4: {"id": 4, "name": "Blender", "category": "Home Appliances", "price": 29.99},
}

#app = FastAPI(default_response_class=ORJSONResponse)
app = FastAPI()
@app.get("/products/search/")
async def search_products(
    q: str = Query(min_length=3),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    results = [
        p for p in products.values()
        if q.lower() in p.name.lower()
        and (category is None or p.category == category)
        and (min_price is None or p.price >= min_price)
        and (max_price is None or p.price <= max_price)
    ]
    return {
        "total": len(results),
        "offset": offset,
        "limit": limit,
        "results": results[offset : offset + limit]
    }


'''
✅ Model Validation (The Right Way in v2)
This is where old code will break.

Pydantic 2 does validation differently. Here’s what it looks like now:
'''
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    birth_date: date
    full_name: Optional[str] = None

    @field_validator("username")
    def check_username(cls, value):
        if not (3 <= len(value) <= 50):
            raise ValueError("Username must be between 3 and 50 chars")
        return value

    @field_validator("password")
    def check_password(cls, val):
        if len(val) < 8:
            raise ValueError("Password must be at least 8 chars")
        return val

    @field_validator("full_name")
    def validate_full_name(cls, val):
        if val and len(val) > 100:
            raise ValueError("Full name exceeds 100 chars")
        return val

#user = UserCreate(username="user1", email="john@gmail.com", password="12345678", birth_date = date.today())

"""
📝 Form Submissions
Still alive and well. Especially in the login world.
"""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "secretpassword":
        return {"access_token": "fake-token", "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Wrong credentials.")



"""
🧩 Nested Request Bodies
If your front end is sending complex objects (think: articles, profiles, orders), you’ll want this structure.
"""

from typing import List, Optional
from pydantic import BaseModel, HttpUrl

class Tag(BaseModel):
    name: str

class Image(BaseModel):
    url: HttpUrl
    caption: Optional[str] = None

class BlogPostCreate(BaseModel):
    title: str
    content: str
    author_id: int
    tags: List[Tag] = []
    images: List[Image] = []

@app.post("/blog/posts")
async def create_blog_post(post: BlogPostCreate):
    return {"message": "Blog post created successfully", "post_id": 123}


"""
📊 Better Query Filtering
Sometimes a client wants the kitchen sink in query options. Things like category filters, pagination, and custom sort orders. All without smashing everything into string parsing.
"""
from typing import List, Optional
from fastapi import Query

@app.get("/products/advanced-search")
async def advanced_search_products(
    q: str = Query(min_length=3),
    categories: List[str] = Query(default_factory=list),
    price_range: Optional[str] = Query(None, pattern=r"^\d+-\d+$"),
    sort_by: str = Query("relevance", enum=["relevance", "price_asc", "price_desc", "newest"]),
    page: int = Query(1, ge=1),
    items_per_page: int = Query(20, ge=1, le=100)
):
    return {
        "message": "Search results",
        "params": {
            "q": q,
            "categories": categories,
            "price_range": price_range,
            "sort_by": sort_by,
            "page": page,
            "items_per_page": items_per_page
        }
    }

"""
🔐 Response Models = Contract Enforcement
FastAPI lets you define exactly what goes back to the client. Somehow, people skip this. Don’t.

That internal_token won’t be included, because response_model filters it out. You’re shipping only what you trust.
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    bio: Optional[str] = None
    interests: List[str] = []

@app.get("/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: int):
    return {
        "id": user_id,
        "username": "johndoe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "bio": "Just another dev",
        "interests": ["testing", "writing blog posts"],
        "internal_token": "SHOULD NOT GET SENT"
    }

"""
🧵 Background Tasks = Non-Blocking Wins
Sometimes you just want to do something after a response is sent without forcing the user to wait.
"""

from fastapi import BackgroundTasks

def send_email(email: str):
    print(f"Sent welcome email to {email}")

@app.post("/users/register")
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, user.email)
    return {"message": "Welcome email queued"}

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