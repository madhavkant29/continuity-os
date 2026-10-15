"""Generate strong local secrets without writing any operator password to disk."""
from __future__ import annotations
import getpass
import hashlib
import os
import secrets
from pathlib import Path

DEST = Path(__file__).resolve().parents[1]/'.env'

def main():
    if DEST.exists():
        raise SystemExit('Configuration already exists; refusing to overwrite .env')
    username=input('Operator username [admin]: ').strip() or 'admin'
    if not username.isascii() or not username.replace('_','').isalnum() or len(username)>64:
        raise SystemExit('Use an alphanumeric username (underscores allowed), up to 64 characters.')
    password=getpass.getpass('Choose a unique operator password (at least 16 characters): ')
    if len(password)<16 or len(password)>256:raise SystemExit('Password must be 16–256 characters.')
    confirm=getpass.getpass('Confirm password: ')
    if password!=confirm:raise SystemExit('Passwords do not match.')
    salt=secrets.token_bytes(16)
    digest=hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=64)
    content=(
        '# Generated local secrets; keep this file private.\n'
        'APP_MODE=demo\n'
        'ENABLE_JUDGE_DEMO=true\n'
        f'APP_LOGIN_USER={username}\n'
        f'APP_LOGIN_PASSWORD_HASH={salt.hex()}:{digest.hex()}\n'
        f'FRONTEND_SESSION_SECRET={secrets.token_urlsafe(48)}\n'
        f'INTERNAL_API_KEY={secrets.token_urlsafe(48)}\n'
        f'FALKOR_PASSWORD={secrets.token_urlsafe(48)}\n'
        'COOKIE_SECURE=false\n'
        'PUBLIC_DOMAIN=app.example.org\n'
        'ENABLE_LLM_ROUTER=false\n'
        'OPENAI_API_KEY=\n'
    )
    fd=os.open(DEST,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    try:
        with os.fdopen(fd,'w') as handle:handle.write(content)
    except Exception:
        DEST.unlink(missing_ok=True)
        raise
    print('Secure configuration created. Password was not saved. Start Docker Compose.')

if __name__=='__main__':main()
