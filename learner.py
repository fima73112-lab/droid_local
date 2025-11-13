from memory import Memory
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
memory = Memory()

def analyze_errors():
    errors = memory.get_recent_errors(5)
    if not errors:
        return "Нет ошибок для анализа."

    text = "\n\n".join(
        [f"Ошибка: {e['error']}\nИсправление: {e['fix']}" for e in errors if e["fix"]]
    )
    prompt = f"""
Ты анализируешь ошибки Python и выводишь закономерности в формате:
<паттерн> => <типичное исправление>

{text}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    learned = response.choices[0].message.content

    for line in learned.splitlines():
        if "=>" in line:
            pattern, fix = line.split("=>", 1)
            memory.learn_pattern(pattern.strip(), fix.strip())

    return learned
