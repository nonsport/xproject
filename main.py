import os
import sys
import asyncio
import importlib.util
from colorama import init
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.table import Table
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style as PTStyle

import apis

# Инициализация
init(autoreset=True)
console = Console()

LOGO_LINES = [
    r"███████╗       ███████╗",
    r"╚███████╗     ███████╔╝",
    r" ╚███████╗   ███████╔╝ ",
    r"  ╚███████╗ ███████╔╝  ",
    r"   ╚██████████████╔╝   ",
    r"    ╚████████████╔╝    ",
    r"    ██████████████╗    ",
    r"   ███████╔████████╗   ",
    r"  ███████╔╝ ╚███████╗  ",
    r" ███████╔╝   ╚███████╗ ",
    r"███████╔╝     ╚███████╗",
    r"╚══════╝       ╚══════╝"
]

DESCRIPTION = "X-Framework | Advanced OSINT Architecture"
PLUGINS_DIR = "plugins"

# --- СИСТЕМА ПЛАГИНОВ ---
loaded_plugins = {}

def load_plugins():
    if not os.path.exists(PLUGINS_DIR):
        os.makedirs(PLUGINS_DIR)
    
    for filename in os.listdir(PLUGINS_DIR):
        if filename.endswith(".py") and not filename.startswith("__"):
            name = filename[:-3]
            filepath = os.path.join(PLUGINS_DIR, filename)
            spec = importlib.util.spec_from_file_location(name, filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            if hasattr(mod, "PLUGIN_NAME") and hasattr(mod, "run"):
                loaded_plugins[name] = mod

# --- ИНТЕРФЕЙС ---
def display_header():
    os.system('clear' if os.name == 'posix' else 'cls')
    
    logo_text = Text("\n".join(LOGO_LINES), style="bold red", justify="center")
    desc_text = Text(DESCRIPTION, style="red", justify="center")
    
    console.print(logo_text)
    console.print(desc_text)
    console.print()

async def run_module(coro, target):
    title = f"❖ Выполнение: {target} ❖"
    console.print(Align.center(Text(title, style="bold red")))
    
    # Использование встроенного спиннера rich
    with console.status("[bold red]Обработка данных (Bypassing & Scraping)...[/bold red]", spinner="bouncingBar"):
        results = await coro
        
    for mod, data in results.items():
        is_error = "error" in str(data).lower()
        color = "red" if is_error else "green"
        icon = "✖" if is_error else "✔"
        
        panel = Panel(
            str(data),
            title=f"[{color}]{icon} {mod}[/{color}]",
            border_style="red",
            expand=False
        )
        console.print(Align.center(panel))
        console.print()

async def menu():
    load_plugins()
    
    # Настройка автозаполнения
    base_commands = ['1', '2', '3', '4', '5', '6', '7', '8', '0', 'IP', 'Domain', 'Phone', 'User', 'Exit']
    plugin_commands = [str(8 + i) for i in range(1, len(loaded_plugins) + 1)]
    completer = WordCompleter(base_commands + plugin_commands, ignore_case=True)
    
    style = PTStyle.from_dict({
        'prompt': 'ansired bold',
        'input': 'ansiwhite'
    })
    session = PromptSession(style=style)

    while True:
        display_header()
        
        # Построение таблицы меню
        table = Table(show_header=False, border_style="red", box=rich.box.ROUNDED)
        table.add_column("ID", style="bold red", justify="right")
        table.add_column("Module", style="white")
        
        table.add_row("[1]", "IP & Infrastructure Search")
        table.add_row("[2]", "Domain & Email Search")
        table.add_row("[3]", "Phone & Identity Search")
        table.add_row("[4]", "Username Global Scan (Deep Dive)")
        table.add_row("[5]", "Google Dorks Generator")
        table.add_row("[6]", "Generate Fake Identity")
        table.add_row("[7]", "Password Generator")
        table.add_row("[8]", "Base64 Encoder / Decoder")
        
        # Динамическое добавление плагинов в меню
        plugin_mapping = {}
        idx = 9
        for p_name, p_mod in loaded_plugins.items():
            table.add_row(f"[{idx}]", f"{p_mod.PLUGIN_NAME} (Plugin)")
            plugin_mapping[str(idx)] = p_mod
            idx += 1
            
        table.add_row("[0]", "[bold red]Exit Framework[/bold red]")
        
        console.print(Align.center(table))
        console.print()

        try:
            choice = await session.prompt_async("➤ X-Terminal > ", completer=completer)
        except (EOFError, KeyboardInterrupt):
            break

        if choice == '1':
            target = await session.prompt_async("❖ Введите IP: ")
            await run_module(apis.scan_ip(target), f"IP: {target}")
        elif choice == '2':
            target = await session.prompt_async("❖ Введите Домен: ")
            await run_module(apis.scan_domain(target), f"Domain: {target}")
        elif choice == '3':
            target = await session.prompt_async("❖ Введите Номер: ")
            await run_module(apis.scan_phone(target), f"Phone: {target}")
        elif choice == '4':
            target = await session.prompt_async("❖ Введите Username: ")
            await run_module(apis.scan_username_deep(target), f"User Deep Dive: {target}")
        elif choice == '5':
            target = await session.prompt_async("❖ Введите Домен для Dorks: ")
            await run_module(apis.google_dorks_scan(target), f"Dorks: {target}")
        elif choice == '6':
            target = await session.prompt_async("❖ Введите локаль [Enter=ru_RU]: ") or 'ru_RU'
            await run_module(apis.get_fake_identity_async(target), f"Identity [{target}]")
        elif choice == '7':
            try:
                length = int(await session.prompt_async("❖ Длина пароля (6-32): "))
                pwd = apis.generate_password(length)
                console.print(Align.center(f"\n[bold green]✔ Сгенерированный пароль: [white]{pwd}"))
            except ValueError:
                console.print(Align.center(f"\n[bold red]✖ Ошибка: Введите число!"))
        elif choice == '8':
            action = await session.prompt_async("❖ [1] Encode | [2] Decode : ")
            text = await session.prompt_async("❖ Введите текст: ")
            if action == '1':
                await run_module(apis.b64_encode(text), "Base64 Encode")
            elif action == '2':
                await run_module(apis.b64_decode(text), "Base64 Decode")
        elif choice in plugin_mapping:
            # Запуск динамического плагина
            target = await session.prompt_async(f"❖ Введите цель для {plugin_mapping[choice].PLUGIN_NAME}: ")
            await run_module(plugin_mapping[choice].run(target), f"Plugin: {plugin_mapping[choice].PLUGIN_NAME}")
        elif choice in ['0', 'Exit', 'exit']:
            os.system('clear' if os.name == 'posix' else 'cls')
            console.print("[bold red]Завершение работы X-Framework...[/bold red]")
            break

        await session.prompt_async("\n[ Enter для возврата в меню ]")

if __name__ == "__main__":
    import rich.box # Локальный импорт для коробки таблиц
    try:
        asyncio.run(menu())
    except KeyboardInterrupt:
        console.print("\n[bold red]Прервано пользователем. Выход...[/bold red]")

