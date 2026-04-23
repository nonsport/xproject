import base64
import asyncio
import aiohttp
import random
import string
from faker import Faker

def d(b): return base64.b64decode(b).decode("utf-8")

S_K = d("VUZ1RWE1V3VQN3lqbEl0UFZucTh6NGRudTRGcGdXV2U=")
C_K = d("Y2Vuc3lzX0VBNGtNVHBhX0JWbVp4ODVvVmZ4SGoyaTF6TFliZm5RZw==")
H_K = d("Yzg0NDBlZjliNzIyZmNhNjg2M2UzNzc3M2YzODE4NTY2ZTk3MjUyNg==")
A_K = d("MGUxMWQ5MjVhY2RmNjcxMmM3MGZlMmVkN2Q3MDkzODQzMTRlNzU2ODhjMmU=")
N_K = d("NDkwYTE5NzliNGE4Y2JiNmJjNDc0YTlmMjU2OTcwYjY=")

def generate_password(length=12):
    length = max(6, min(32, length))
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    special = "!@#$%^&*()-_+="

    password = [
        random.choice(lower),
        random.choice(upper),
        random.choice(digits),
        random.choice(special)
    ]
    all_chars = lower + upper + digits + special
    password += [random.choice(all_chars) for _ in range(length - 4)]
    random.shuffle(password)
    return ''.join(password)

async def get_fake_identity_async(locale='ru_RU'):
    fake = Faker(locale)
    return {
        "Fake_Profile": {
            "full_name": fake.name(),
            "address": fake.address().replace('\n', ', '),
            "phone": fake.phone_number(),
            "email": fake.email(),
            "birth_date": fake.date_of_birth().strftime("%d.%m.%Y"),
            "company": fake.company(),
            "job": fake.job(),
            "username": fake.user_name(),
            "password": generate_password(16),
            "credit_card": fake.credit_card_full(),
            "user_agent": fake.user_agent(),
            "ip": fake.ipv4()
        }
    }

async def fetch_json(session, url, headers=None, params=None, auth=None):
    try:
        async with session.get(url, headers=headers, params=params, auth=auth, timeout=12) as response:
            if response.status == 200:
                return await response.json()
            return {"error": f"HTTP {response.status}"}
    except Exception as e:
        return {"error": str(e)}

async def google_dorks_scan(domain):
    dorks = [
        {"target": "Public Files", "query": f"site:{domain} ext:pdf OR ext:doc OR ext:txt OR ext:xlsx"},
        {"target": "Config & Env", "query": f"site:{domain} ext:env OR ext:conf OR ext:sql OR ext:ini"},
        {"target": "Login Pages", "query": f"site:{domain} inurl:login OR inurl:admin OR inurl:auth"},
        {"target": "Directory Listing", "query": f"site:{domain} intitle:index.of"},
        {"target": "Exposed DBs", "query": f"site:{domain} inurl:phpmyadmin OR inurl:db"}
    ]
    results = []
    for dork in dorks:
        encoded = dork['query'].replace(" ", "+").replace(":", "%3A")
        results.append({
            "category": dork['target'],
            "dork": dork['query'],
            "url": f"https://www.google.com/search?q={encoded}"
        })
    return {"Google_Dorks_Links": results}

async def b64_encode(text):
    return {"Base64_Encode": {"original": text, "result": base64.b64encode(text.encode('utf-8')).decode('utf-8')}}

async def b64_decode(text):
    try:
        return {"Base64_Decode": {"original": text, "result": base64.b64decode(text.encode('utf-8')).decode('utf-8')}}
    except Exception as e:
        return {"Base64_Decode": {"error": f"Неверный формат Base64: {str(e)}"}}

async def search_ddg(query):
    encoded_query = query.replace(" ", "+")
    return [{"info": "Search link generated", "url": f"https://duckduckgo.com/?q={encoded_query}"}]

async def check_ip_shodan(session, ip):
    return await fetch_json(session, f"https://api.shodan.io/shodan/host/{ip}", params={"key": S_K})

async def check_ip_censys(session, ip):
    headers = {"Accept": "application/json", "Authorization": f"Bearer {C_K}"}
    return await fetch_json(session, f"https://search.censys.io/api/v2/hosts/{ip}", headers=headers)

async def check_ip_abuseipdb(session, ip):
    headers = {"Accept": "application/json", "Key": A_K}
    return await fetch_json(session, "https://api.abuseipdb.com/api/v2/check", headers=headers, params={"ipAddress": ip})

async def search_domain_hunter(session, domain):
    return await fetch_json(session, "https://api.hunter.io/v2/domain-search", params={"domain": domain, "api_key": H_K})

async def check_phone_numverify(session, phone):
    return await fetch_json(session, "http://apilayer.net/api/validate", params={"access_key": N_K, "number": phone})

async def scan_username(username):
    sites = {
        "GitHub": f"https://github.com/{username}",
        "Twitter/X": f"https://x.com/{username}",
        "Telegram": f"https://t.me/{username}",
        "Reddit": f"https://www.reddit.com/user/{username}"
    }
    results = {}
    async with aiohttp.ClientSession() as session:
        for name, url in sites.items():
            try:
                async with session.get(url, timeout=5) as resp:
                    results[name] = {"url": url, "status": "Найден" if resp.status == 200 else "Не найден"}
            except:
                results[name] = {"url": url, "status": "Ошибка"}
    return {"Username_Scan": results}

async def scan_ip(ip):
    async with aiohttp.ClientSession() as session:
        tasks = [check_ip_shodan(session, ip), check_ip_censys(session, ip), check_ip_abuseipdb(session, ip)]
        res = await asyncio.gather(*tasks)
        return {"Shodan": res[0], "Censys": res[1], "AbuseIPDB": res[2]}

async def scan_domain(domain):
    links = await search_ddg(f"site:{domain}")
    async with aiohttp.ClientSession() as session:
        hunter = await search_domain_hunter(session, domain)
    return {"Search_Links": links, "Hunter_Emails": hunter}

async def scan_phone(phone):
    async with aiohttp.ClientSession() as session:
        num = await check_phone_numverify(session, phone)
    links = await search_ddg(f'"{phone}"')
    return {"Numverify": num, "Web_Mentions": links}
