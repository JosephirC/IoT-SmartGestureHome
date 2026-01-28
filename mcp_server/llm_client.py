import os
import asyncio
import httpx
from fastmcp import Client
from fastmcp.client.transports import StdioTransport


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_URL = f"{OLLAMA_HOST.rstrip('/')}/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")


async def llm_decide_tool(user_text: str):
    """Use Ollama (Llama 3.1 8B) Instruct to decide which tool to call."""
    prompt = f"""Given this user input, decide which home automation command to execute.
User: "{user_text}"

Respond with ONLY one of these exact formats:
- control_door OPEN
- control_door CLOSE
- control_fans ON
- control_fans OFF
- control_leds ON
- control_leds OFF
- none

Response:"""

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 16,
                },
            },
        )
        resp.raise_for_status()
        completion = resp.json().get("response", "").strip().upper()
        print(f"[DEBUG] LLM response: {completion}")

    # Parse tool and action from response (use split to avoid substring matches)
    lines = completion.split('\n')
    first_line = lines[0].strip()

    if "CONTROL_DOOR" in first_line:
        action = "OPEN" if " OPEN" in first_line else "CLOSE"
        return "control_door", {"action": action}
    if "CONTROL_FANS" in first_line:
        action = "ON" if " ON" in first_line else "OFF"
        return "control_fans", {"action": action}
    if "CONTROL_LEDS" in first_line:
        action = "ON" if " ON" in first_line else "OFF"
        return "control_leds", {"action": action}
    return None, None


async def main():
    transport = StdioTransport(
        command="fastmcp",
        args=["run", "server.py:mcp"]
    )

    client = Client(transport)

    async with client:
        print("LLM connecté au MCP.")

        while True:
            user_text = input(">> ")
            tool, args = await llm_decide_tool(user_text)

            if tool is None:
                print("Action non comprise.")
                continue

            result = await client.call_tool(tool, args)
            print(result.content[0].text if result.content else str(result))


if __name__ == "__main__":
    asyncio.run(main())
