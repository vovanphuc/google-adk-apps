import json
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

load_dotenv('../../.env')

# --- Constants ---
AGENT_NAME_CAFE = "cafe_order_agent"
GEMINI_MODEL = "gemini-2.0-flash" # Example model name, replace with actual model name if different

# --- Load OpenAPI Specification for Café API ---
# from http://127.0.0.1:5000/openapi.json when your FastAPI server is running.
current_dir = os.path.dirname(os.path.abspath(__file__))
spec_file_path = os.path.join(current_dir, 'openapi_spec.json')

print(f"Loading OpenAPI spec from: {spec_file_path}")

with open(spec_file_path, 'r') as spec_file:
    openapi_spec = json.load(spec_file)
    openapi_spec_string = json.dumps(openapi_spec)

# --- Create OpenAPIToolset ---
generated_tools_list = []
try:
    # Instantiate the toolset with the spec string
    cafe_toolset = OpenAPIToolset(
        spec_str=openapi_spec_string,
        spec_str_type="json"
    )
    # Get all tools generated from the spec
    generated_tools_list = cafe_toolset.get_tools()
    print(f"Generated {len(generated_tools_list)} tools from Café OpenAPI spec:")
    for tool in generated_tools_list:
        # Tool names are snake_case versions of operationId from FastAPI
        print(f"- Tool Name: '{tool.name}', Description: {tool.description[:80]}...") # Use tool.description

except ValueError as ve:
    print(f"Validation Error creating OpenAPIToolset: {ve}")
except Exception as e:
    print(f"Unexpected Error creating OpenAPIToolset: {e}")
    # Potentially exit or skip agent creation if tools fail

# --- Agent Definition ---
root_agent = LlmAgent(
    name=AGENT_NAME_CAFE,
    model=GEMINI_MODEL,
    tools=generated_tools_list, # Pass the list of RestApiTool objects
    instruction=f"""You are a Café Assistant helping users view the menu and place orders using an API.
    Use the available tools to fulfill user requests.
    Available tools: {', '.join([t.name for t in generated_tools_list])}.

    - To show the menu, use the 'get_menu_menu_get' tool.
    - To place an order, use the 'create_order_orders_post' tool. You will need a list of dish IDs from the menu. Ask the user for confirmation if needed.
    - To see all past orders, use the 'get_all_orders_orders_get' tool.
    - To see a specific order, use the 'get_order_by_id_orders__order_id__get' tool with the order's ID.

    Confirm the order details (items, total price, order ID) back to the user after placing an order.
    When showing the menu, list the items with their ID, name, price, and description.
    """,
    description="Manages Café Menu viewing and ordering using tools generated from the FastAPI OpenAPI spec."
)
