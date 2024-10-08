"""
Script to test the proxy's ability to support response streaming when functions are used.

Tested with openai package version 1.35.10.
"""

import argparse
import json

from openai import AzureOpenAI

parser = argparse.ArgumentParser()
parser.add_argument(
    "--powerproxy-endpoint", type=str, default="http://localhost", help="Path to PowerProxy/Azure OpenAI endpoint"
)
parser.add_argument(
    "--api-key", type=str, default="04ae14bc78184621d37f1ce57a52eb7", help="API key to access PowerProxy"
)
parser.add_argument("--deployment-name", type=str, default="gpt-4o", help="Name of Azure OpenAI deployment to test")
parser.add_argument(
    "--api-version", type=str, default="2024-06-01", help="API version to use when accessing Azure OpenAI"
)
args, unknown = parser.parse_known_args()

client = AzureOpenAI(
    azure_endpoint=args.powerproxy_endpoint,
    api_version=args.api_version,
    api_key=args.api_key,
)

function_name = ""
arguments = ""
for chunk in client.chat.completions.create(
    model=args.deployment_name,
    messages=[
        {
            "role": "user",
            # "content": "Find beachfront hotels in San Diego for less than $300 a month with free breakfast.",
            "content": "Book Palace Beach, starting Feb 14 to Feb 18.",
        }
    ],
    tools=[
        {
            "type": "function",
            "function": {
                "name": "search_hotels",
                "description": "Retrieves hotels from the search index based on the parameters provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location of the hotel (i.e. Seattle, WA)",
                        },
                        "max_price": {
                            "type": "number",
                            "description": "The maximum price for the hotel",
                        },
                        "features": {
                            "type": "string",
                            "description": "A comma separated list of features (i.e. beachfront, free wifi, etc.)",
                        },
                    },
                    "required": ["location"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "book_hotel",
                "description": "Books a hotel based on the parameters provided.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the hotel (i.e. Palace Beach)",
                        },
                        "start_date": {
                            "type": "string",
                            "description": "The start date of the booking.",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "The end date of the booking.",
                        },
                    },
                    "required": ["name", "start_date", "end_date"],
                },
            },
        },
    ],
    temperature=0,
    tool_choice="auto",
    stream=True,
):
    if "ChoiceDeltaToolCallFunction" in f"{chunk}":
        function_name += chunk.choices[0].delta.tool_calls[0].function.name or ""
        arguments += chunk.choices[0].delta.tool_calls[0].function.arguments or ""


def search_hotels(location, max_price, features):
    """Searches for hotels."""
    print("Hi there -- this is function search_hotels(). I was invoked with the following commands:")
    print(f"Location: {location}, max price {max_price}, features: {features}")


def book_hotel(name, start_date, end_date):
    """Books a hotel."""
    print("Hi there -- this is function book_hotel(). I was invoked with the following commands:")
    print(f"Booking hotel '{name}'. Start date: {start_date}, End date: {end_date}")


print(f"Function Name: {function_name}")
print(f"Arguments: {arguments}")

match function_name:
    case "search_hotels":
        search_hotels(**(json.loads(arguments)))
    case "book_hotel":
        book_hotel(**(json.loads(arguments)))
    case _:
        raise ValueError(f"Function name '{function_name}' is not available.")
