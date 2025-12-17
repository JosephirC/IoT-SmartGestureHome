import asyncio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


def llm_decide_tool(user_text: str):
    text = user_text.lower()

    if "porte" in text:
        return "open_door", {}
    elif "ventilateur" in text:
        return "turn_on_fan", {}
    elif "led" in text:
        return "turn_on_leds", {}
    return None, None


async def main():
    transport = StdioTransport(
        command="fastmcp",
        args=["run", "mcp_server/server.py:mcp"]
    )

    client = Client(transport)

    async with client:
        print("LLM connecté au MCP.")

        while True:
            user_text = input(">> ")
            tool, args = llm_decide_tool(user_text)

            if tool is None:
                print("Action non comprise.")
                continue

            result = await client.call_tool(tool, args)
            print(result)


if __name__ == "__main__":
    asyncio.run(main())
