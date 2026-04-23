import base64
import asyncio
import aiohttp
import random
import string
import re
from faker import Faker

def d(b): return base64.b64decode(b).decode("utf-8")

# Зашифрованные ключи
S_K = d("VUZ1RWE1V3VQN3lqbEl0UFZucTh6NGRudTRGcGdXV2U=")
C_K = d("Y2Vuc3lzX0VBNGtNVHBhX0JWbVp4ODVvVmZ4SGoyaTF6TFliZm5RZw==")
H_K = d("Yzg0NDBlZjliNzIyZmNhNjg2M2UzNzc3M2YzODE4NTY2ZTk3MjUyNg==")
A_K = d("MGUxMWQ5MjVhY2RmNjcxMmM3MGZlMmVkN2Q3MDkzODQzMTRlNzU2ODhjMmU=")
N_K = d("NDkwYTE5NzliNGE4Y2JiNmJjNDc0YTlmMjU2OTcwYjY=")

# --- User-Agent Spoofer ---
UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
]

def get_headers():
    return {
        "User-Agent": random.choice(UAS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }

def generate_password(length=12):
    length = max(6, min(32, length))
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*()-_+="
    password = [random.choice(c) for c in (string.ascii_lowercase, string.ascii_uppercase, string.digits, "!@#$%^&*()-_+=")]
    password += [random.choice(all_chars) for _ in range(length - 4)]
    random.shuffle(password)
    return ''.join(password)

async def get_fake_identity_async(locale='ru_RU'):
    fake = Faker(locale)
    return {
        "Fake_Profile": {
            "Name": fake.name(),
            "Address": fake.address().replace('\n', ', '),
            "Phone": fake.phone_number(),
            "Email": fake.email(),
            "Company": fake.company(),
            "IP": fake.ipv4()
        }
    }

async def fetch_json(session, url, headers=None, params=None):
    try:
        async with session.get(url, headers=headers or get_headers(), params=params, timeout=12) as response:
            if response.status == 200:
                return await response.json()
            return {"error": f"HTTP {response.status}"}
    except Exception as e:
        return {"error": str(e)}

# --- Deep Dive Соцсети без API ---
async def scan_username_deep(username):
    sites = {
        "GitHub": f"https://github.com/{username}",
        "Linktree": f"https://linktr.ee/{username}",
        "TryHackMe": f"https://tryhackme.com/p/{username}",
        "Pastebin": f"https://pastebin.com/u/{username}"
    }
    results = {}
    
    async with aiohttp.ClientSession(headers=get_headers()) as session:
        for name, url in sites.items():
            try:
                async with session.get(url, timeout=7) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        
                        # Вытягиваем Title
                        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
                        title = title_match.group(1).strip() if title_match else "Нет заголовка"
                        
                        # Вытягиваем Meta Description (Bio)
                        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
                        bio = desc_match.group(1).strip() if desc_match else "Описание скрыто"
                        
                        results[name] = {
                            "Status": "✅ Найден",
                            "URL": url,
                            "Title": title,
                            "Bio": bio[:100] + "..." if len(bio) > 100 else bio
                        }
                    else:
                        results[name] = {"Status": f"❌ Не найден (HTTP {resp.status})"}
            except Exception as e:
                results[name] = {"Status": f"⚠️ Ошибка соединения"}
                
    return {"Deep_OSINT_Scan": results}

# --- Остальные модули ---
async def google_dorks_scan(domain):
    return {"Google_Dorks": [
        {"Target": "Config", "URL": f"https://www.google.com/search?q=site:{domain}+ext:env+OR+ext:sql"},
        {"Target": "Login", "URL": f"https://www.google.com/search?q=site:{domain}+inurl:login+OR+inurl:admin"}
    ]}

async def b64_encode(text):
    return {"Base64_Encode": {"Result": base64.b64encode(text.encode('utf-8')).decode('utf-8')}}

async def b64_decode(text):
    try:
        return {"Base64_Decode": {"Result": base64.b64decode(text.encode('utf-8')).decode('utf-8')}}
    except:
        return {"Base64_Decode": {"Error": "Invalid Base64"}}

async def scan_ip(ip):
    async with aiohttp.ClientSession() as session:
        shodan = await fetch_json(session, f"https://api.shodan.io/shodan/host/{ip}", params={"key": S_K})
        abuse = await fetch_json(session, "https://api.abuseipdb.com/api/v2/check", headers={"Key": A_K}, params={"ipAddress": ip})
        return {"Shodan": shodan, "AbuseIPDB": abuse}

async def scan_domain(domain):
    async with aiohttp.ClientSession() as session:
        hunter = await fetch_json(session, "https://api.hunter.io/v2/domain-search", params={"domain": domain, "api_key": H_K})
        return {"Hunter_Emails": hunter}

async def scan_phone(phone):
    async with aiohttp.ClientSession() as session:
        num = await fetch_json(session, "http://apilayer.net/api/validate", params={"access_key": N_K, "number": phone})
        return {"Numverify": num}

