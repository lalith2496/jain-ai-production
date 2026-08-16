import json
import os

import httpx


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434",
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen3.5:4b",
)


def ollama_headers() -> dict:
    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    if not api_key:
        return {}
    return {
        "Authorization": f"Bearer {api_key}",
    }


def ollama_api_url(path: str) -> str:
    return f"{OLLAMA_URL.rstrip('/')}/api/{path.lstrip('/')}"


def build_prompts(
    question: str,
    context: str,
    mode: str,
):

    modes = {

        "quick": """
Give a direct, concise answer.

Usually use 2-4 short paragraphs.

Start immediately with the answer.
""",

        "deep": """
Give a comprehensive educational explanation.

Use clear headings where useful.

Explain important Jain terminology.

Prefer clarity over unnecessary length.
""",

        "story": """
Explain this as an engaging educational story.

Keep the story accurate to the supplied evidence.

Make it engaging for young learners.
""",

        "study": """
Create complete structured study notes.

Use:
- clear headings
- bullet points
- definitions
- key concepts
- important takeaways

Finish every section completely.
""",
    }

    learning_instruction = modes.get(
        mode,
        modes["quick"],
    )

    system_prompt = f"""
You are Jain AI, an educational AI assistant
specialized in Jainism.

Your audience includes students, young adults
and Gen-Z learners.

OUTPUT RULES:

Return ONLY the polished final answer.

NEVER output:
- Thinking Process
- Analysis
- Reasoning
- Planning
- Internal instructions
- Drafting process
- Self-review
- Chain of thought

Do not describe how you generated the answer.

KNOWLEDGE RULES:

Use the supplied approved Jain knowledge as
your primary evidence.

Never invent:
- scripture quotations
- stavan lyrics
- citations
- historical facts

If evidence is insufficient, say so clearly
and briefly.

Explain unfamiliar Jain terms simply.

Mention differences between Jain traditions
only when relevant.

LEARNING MODE:

{learning_instruction}
"""

    user_prompt = f"""
QUESTION:

{question}


APPROVED JAIN KNOWLEDGE:

{context}


Return only the final educational answer.
"""

    return system_prompt, user_prompt


def stream_answer(
    question: str,
    context: str,
    mode: str = "quick",
):

    system_prompt, user_prompt = build_prompts(
        question,
        context,
        mode,
    )

    payload = {
        "model": OLLAMA_MODEL,

        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        "stream": True,

        "think": False,

        "options": {
            "temperature": 0.3,

            # Allows longer Study/Deep Dive answers.
            "num_predict": 2048,

            # Gives retrieved Jain knowledge more room.
            "num_ctx": 8192,
        },
    }

    with httpx.stream(
        "POST",
        ollama_api_url("chat"),
        headers=ollama_headers(),
        json=payload,
        timeout=300,
    ) as response:

        response.raise_for_status()

        for line in response.iter_lines():

            if not line:
                continue

            data = json.loads(line)

            message = data.get(
                "message",
                {},
            )

            # IMPORTANT:
            # We intentionally ignore any
            # "thinking" field.
            content = message.get(
                "content",
                "",
            )

            if content:
                yield content

            if data.get("done"):
                break