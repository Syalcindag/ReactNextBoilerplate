import os
import requests
import json

# Google Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# GitHub değişkenlerini al
repo_full = os.getenv("GITHUB_REPOSITORY")  # "owner/repo" formatında gelir
owner, repo_name = repo_full.split("/")  # owner ve repo ayrıştırılıyor

# PR numarasını al
event_path = os.getenv("GITHUB_EVENT_PATH")
try:
    with open(event_path, 'r') as f:
        event_data = json.load(f)
        pr_number = event_data["pull_request"]["number"]
except (FileNotFoundError, KeyError):
    print("❌ PR numarası bulunamadı! Çıkılıyor...")
    exit(1)

print(f"✅ Doğru PR numarası alındı: {pr_number}")

# PR değişikliklerini al
headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/files"

print(f"DEBUG: GitHub API URL = {url}")

response = requests.get(url, headers=headers)

# API Yanıtını kontrol et
try:
    files = response.json()
    if not isinstance(files, list):  # Eğer JSON beklenen formatta değilse
        print("❌ API yanıtı beklenenden farklı:", files)
        exit(1)
except Exception as e:
    print(f"❌ API yanıtı çözümlenemedi: {e}")
    exit(1)

# Değişiklikleri işle
changed_code = []
file_changes = {}  # Dosya adı -> diff map
for file in files:
    if isinstance(file, dict) and "filename" in file and "patch" in file:
        filename = file["filename"]
        patch = file["patch"]
        changed_code.append(f"### {filename}\n{patch}")
        file_changes[filename] = patch  # Dosya diff'i kaydet

if not changed_code:
    print("✅ No code changes detected.")
    exit(0)

code_review_prompt = f"""
Aşağıdaki kod değişikliklerini inceleyerek **her dosya için en kritik 3 hatayı** veya **iyileştirme fırsatını** listele. 
Her öneri **kod kalitesi, güvenlik veya performans açısından önemli** olmalıdır.

Kod değişiklikleri:
{''.join(changed_code)}

Format:
Filename: file_name.py
1. [Kısa başlık] - Açıklama (İlgili kod satırını belirt)

Filename: another_file.js
1. [Kısa başlık] - Açıklama (İlgili kod satırını belirt)
"""

# Google Gemini API'ye istek gönder
gemini_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

payload = {
    "contents": [
        {"parts": [{"text": code_review_prompt}]}
    ]
}

headers = {"Content-Type": "application/json"}

print("🔍 Google Gemini API'ye istek gönderiliyor...")
gemini_response = requests.post(gemini_url, headers=headers, json=payload)

# API Yanıtını kontrol et
try:
    gemini_data = gemini_response.json()
    print("🔍 Google Gemini API Yanıtı:", gemini_data)  # DEBUG: Gelen JSON'u ekrana yazdır
    ai_review = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
except Exception as e:
    print(f"❌ Google Gemini yanıtı çözümlenemedi: {e}")
    exit(1)

# PR’a satır bazlı yorumlar ekle
comment_url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}/comments"

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    "X-GitHub-Api-Version": "2022-11-28"
}

# AI yorumunu işleyerek her dosyanın ilgili satırına ekleyelim
current_file = None  # Hata almamak için başlatıyoruz

for line in ai_review.split("\n"):
    if line.startswith("Filename:"):
        current_file = line.split(" ")[1].strip()
    elif line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
        # Öneriyi ve satır numarasını çıkarmaya çalış
        suggestion = line.split(" - ")[1].strip() if " - " in line else line.strip()
        line_number = None

        # Dosyanın diff'inde hangi satıra denk geldiğini bul
        if current_file and current_file in file_changes:
            patch_lines = file_changes[current_file].split("\n")
            for i, patch_line in enumerate(patch_lines):
                if patch_line.startswith("+") and not patch_line.startswith("+++"):
                    line_number = i  # İlk değişiklik satırını al
                    break

        if line_number is not None:
            comment_data = {
                "body": f"🔍 **AI Review:** {suggestion}",
                "commit_id": event_data["pull_request"]["head"]["sha"],
                "path": current_file,
                "side": "RIGHT",
                "line": line_number
            }

            print(f"DEBUG: Gönderilen PR Satır Yorumu: {comment_data}")
            comment_response = requests.post(comment_url, headers=headers, json=comment_data)

            # Yorum ekleme başarılı mı kontrol et
            if comment_response.status_code == 201:
                print("✅ PR'a satır bazlı yorum başarıyla eklendi!")
            else:
                print(f"❌ PR'a yorum eklenemedi! Hata Kodu: {comment_response.status_code}, Yanıt: {comment_response.json()}")

print("✅ AI Review tamamlandı, yorumlar PR’a eklendi!")
