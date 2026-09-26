import urllib.parse
import requests
import sys
import os

# sys.path
sys.path.insert(0, "/home/ubuntu")
from Loker.config.settings import settings

SCOPES = ["https://www.googleapis.com/auth/blogger"]
REDIRECT_URI = "https://developers.google.com/oauthplayground"


def generate_auth_url():
    client_id = settings.BLOGGER_CLIENT_ID
    if not client_id:
        print("ERROR: BLOGGER_CLIENT_ID belum diatur di .env")
        return

    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    print("\n" + "=" * 70)
    print("LANGKAH OTORISASI GOOGLE BLOGGER OAUTH 2.0")
    print("=" * 70)
    print("1. Pastikan di Google Cloud Console pada OAuth Client ID:")
    print(f"   Authorized Redirect URIs mencakup: {REDIRECT_URI}")
    print("\n2. Buka link otorisasi berikut di browser:")
    print(f"\n{url}\n")
    print("3. Login dengan akun Google pemilik blogspot.")
    print("4. Setelah izinkan akses, Anda akan dialihkan ke OAuth Playground.")
    print("5. Salin 'Authorization code' yang didapat, lalu jalankan:")
    print("   python /home/ubuntu/Loker/scripts/blogger_auth.py --code <AUTHORIZATION_CODE>")
    print("=" * 70 + "\n")


def exchange_code_for_token(code: str):
    client_id = settings.BLOGGER_CLIENT_ID
    client_secret = settings.BLOGGER_CLIENT_SECRET
    
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    
    res = requests.post(token_url, data=payload)
    if res.status_code == 200:
        data = res.json()
        refresh_token = data.get("refresh_token")
        access_token = data.get("access_token")
        print("\n✅ Otorisasi Berhasil!")
        print(f"Access Token  : {access_token[:20]}...")
        if refresh_token:
            print(f"Refresh Token : {refresh_token}")
            print("\nSilakan tambahkan ke .env:")
            print(f"BLOGGER_REFRESH_TOKEN={refresh_token}")
        else:
            print("⚠️ Tidak ada refresh_token (mungkin sebelumnya sudah pernah diotorisasi tanpa revoke prompt).")
    else:
        print(f"❌ Gagal menukar kode: {res.status_code}")
        print(res.text)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--code":
        exchange_code_for_token(sys.argv[2])
    else:
        generate_auth_url()
