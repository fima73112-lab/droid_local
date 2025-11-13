import subprocess, os, typer
from rich.console import Console
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from openai import OpenAI
from memory import Memory
from learner import analyze_errors

console = Console()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
memory = Memory()

def run_code(file):
    try:
        subprocess.run(["python", file], check=True)
        console.print("[green]✅ Код выполнен без ошибок[/green]")
        memory.add("run", f"Успешный запуск {file}")
    except subprocess.CalledProcessError as e:
        console.print("[red]❌ Ошибка исполнения[/red]")
        console.print(e)
        memory.add("error", "Ошибка исполнения", file_name=file, error=str(e))
        fix_code(file, str(e))

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def fix_code(file, error):
    pattern_fix = memory.find_pattern(error)
    if pattern_fix:
        console.print("[yellow]⚡ Применяю известное исправление[/yellow]")
        with open(file, "r") as f:
            content = f.read().replace("TODO", pattern_fix)
        with open(file, "w") as f:
            f.write(content)
        run_code(file)
        return

    with open(file, "r") as f:
        content = f.read()

    prompt = f"""
Ошибка:
{error}

Код:
{content}

Исправь код и выведи исправленную версию полностью.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    fixed_code = response.choices[0].message.content

    with open(file, "w") as f:
        f.write(fixed_code)

    memory.add("fix", "Исправлен код", file_name=file, fix=fixed_code[:300])
    console.print("[yellow]🧠 Код исправлен. Повторный запуск...[/yellow]")
    run_code(file)

def interpret_command(command: str):
    """Определяет, что делать с введённым текстом"""
    cmd = command.lower()

    if "обучи" in cmd or "learn" in cmd:
        console.print("[cyan]📚 Анализ ошибок...[/cyan]")
        console.print(analyze_errors())

    elif "запусти" in cmd or "run" in cmd:
        parts = cmd.split()
        file = next((p for p in parts if p.endswith(".py")), None)
        if file:
            run_code(file)
        else:
            console.print("[red]Не указан файл для запуска[/red]")

    elif "история" in cmd or "history" in cmd:
        for h in memory.data["history"][-10:]:
            console.print(f"[dim]{h['timestamp']}[/dim] | [bold]{h['type']}[/bold]: {h['description']}")

    else:
        create_task(command)

def create_task(task: str):
    timestamp = datetime.now().strftime("%H%M%S")
    file_name = f"script_{timestamp}.py"
    context = memory.get_context(10)
    console.print(f"[cyan]🧩 Генерация кода для задачи:[/cyan] {task}")

    prompt = f"""
Контекст проекта:
{context}

Создай Python-код для задачи:
{task}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    code = response.choices[0].message.content

    with open(file_name, "w") as f:
        f.write(code)

    console.print(f"[green]✅ Код сохранён в {file_name}[/green]")
    memory.add("create", f"Создана задача: {task}", file_name=file_name)
    run_code(file_name)

def main():
    console.print("[bold cyan]🤖 Droid Local v3 — интерактивный агент[/bold cyan]")
    console.print("Введите задачу (или 'выход' для завершения)\n")

    while True:
        command = console.input("[yellow]🟢 >> [/yellow]").strip()
        if command.lower() in ("выход", "exit", "quit"):
            console.print("[red]🚪 Завершение работы[/red]")
            break
        interpret_command(command)

if __name__ == "__main__":
    main()
