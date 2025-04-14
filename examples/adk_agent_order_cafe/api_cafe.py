from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import uuid 

app = FastAPI(
    title="Café Ordering API",
    description="An API to manage café menu and orders, now with dish descriptions!",
    version="1.0.0", # Bumped version
)

menu_db: Dict[int, Dict[str, float | str]] = {
    1: {"name": "Espresso", "price": 2.50, "description": "Strong and concentrated coffee shot."},
    2: {"name": "Cappuccino", "price": 3.50, "description": "Espresso with steamed milk foam."},
    3: {"name": "Latte", "price": 3.75, "description": "Espresso with more steamed milk and a light layer of foam."},
    4: {"name": "Croissant", "price": 2.00, "description": "Buttery, flaky, viennoiserie pastry."},
    5: {"name": "Muffin", "price": 2.25, "description": "Sweet individual-sized baked good (Blueberry)."},
    6: {"name": "Iced Tea", "price": 3.00, "description": "Chilled black tea, lightly sweetened."},
}

orders_db: List[Dict] = []

class Dish(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None 

class OrderRequest(BaseModel):
    dish_ids: List[int] = Field(..., examples=[[1, 4, 4]]) 

class OrderItem(BaseModel):
    dish_id: int
    name: str
    price: float # Price per unit when ordered
    quantity: int

class Order(BaseModel):
    order_id: str # Using UUID string for unique IDs
    items: List[OrderItem]
    total_price: float
    status: str = "received" # Simple status tracking


@app.get("/menu", response_model=List[Dish], tags=["Menu"])
async def get_menu():
    """
    Retrieves the list of available dishes from the café menu,
    including their descriptions.
    """

    menu_list = []
    for dish_id, details in menu_db.items():
        menu_list.append(Dish(id=dish_id, **details)) 
    return menu_list

@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(order_request: OrderRequest):
    """
    Places a new order.

    Takes a list of dish IDs, validates them, calculates the total price,
    and returns the created order details. Description is not included in the order itself.
    """
    order_items: List[OrderItem] = []
    total_price: float = 0.0
    item_counts: Dict[int, int] = {} # To count quantity of each dish ID

    # Count occurrences of each dish ID in the request
    for dish_id in order_request.dish_ids:
        item_counts[dish_id] = item_counts.get(dish_id, 0) + 1

    # Validate dish IDs and calculate totals
    for dish_id, quantity in item_counts.items():
        if dish_id not in menu_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dish with ID {dish_id} not found in the menu.",
            )
        # We only need name and price from menu_db for the order item
        dish_details = menu_db[dish_id]
        item_price = dish_details["price"] * quantity
        order_items.append(
            OrderItem(
                dish_id=dish_id,
                name=dish_details["name"],
                price=dish_details["price"], # Price per unit
                quantity=quantity
            )
        )
        total_price += item_price

    if not order_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an empty order. Please provide dish IDs.",
        )

    # Create the new order object
    new_order = Order(
        order_id=str(uuid.uuid4()), # Generate a unique ID
        items=order_items,
        total_price=round(total_price, 2), # Round to 2 decimal places
        status="received",
    )

    orders_db.append(new_order.model_dump()) 

    return new_order 


@app.get("/orders", response_model=List[Order], tags=["Orders"])
async def get_all_orders():
    """
    Retrieves a list of all orders that have been placed.
    """
    # Convert the stored dictionaries back into Order models
    return [Order(**order_data) for order_data in orders_db]


@app.get("/orders/{order_id}", response_model=Order, tags=["Orders"])
async def get_order_by_id(order_id: str):
    """
    Retrieves the details of a specific order by its unique ID.
    """
    for order_data in orders_db:
        if order_data["order_id"] == order_id:
            return Order(**order_data) # Convert dict back to Order model

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Order with ID {order_id} not found.",
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)