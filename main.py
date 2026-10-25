import argparse
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from call_function import available_functions, call_function
from prompts import system_prompt


def main():
    parser = argparse.ArgumentParser(description="CLI tool for AI completion")
    parser.add_argument("user_prompt", type=str, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OpenRouter api key was not set!")

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": args.user_prompt},
    ]

    for _ in range(20):
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            tools=available_functions,
            temperature=0,
        )

        if getattr(response, "usage", None) is None:
            raise RuntimeError("API request failed or did not return usage metadata")

        if args.verbose:
            print(f"User prompt: {args.user_prompt}")
            print(f"Prompt tokens: {response.usage.prompt_tokens}")
            print(f"Response tokens: {response.usage.completion_tokens}")

        message = response.choices[0].message
        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                result_message = call_function(tool_call, verbose=args.verbose)

                if not result_message.get("content"):
                    raise RuntimeError("Tool response content is missing or empty")

                messages.append(result_message)

                if args.verbose:
                    print(f"-> {result_message['content']}")
        else:
            print(message.content)
            return

    print("Error: Reached maximum loop iterations without a final response")
    sys.exit(1)


if __name__ == "__main__":
    main()
