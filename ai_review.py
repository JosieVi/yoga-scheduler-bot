import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def review_code():
    try:
        with open("main.py", "r", encoding="utf-8") as f:
            code = f.read()
    except FileNotFoundError:
        print(
            "Error: 'main.py' not found. Please ensure the file exists in the current directory."
        )
        return

    prompt = f"""
    You are a senior Python developer and a QA Automation Engineer.
    Review the following code for errors, logical flaws, and bad practices.
    Pay special attention to database interactions and exception handling.
    Provide a concise response: a list of critical issues and one improvement tip.

    Code to review:
    {code}
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash-latest", contents=prompt
    )

    print("--- AI CODE REVIEW RESULTS ---")
    print(response.text)


if __name__ == "__main__":
    review_code()
