from urllib.parse import urlparse,urlunparse
from config import ALLOWED_NETWORK_SCHEMES

def validate_url(url):
    p=urlparse(url.strip())
    if p.scheme.lower() not in ALLOWED_NETWORK_SCHEMES or not p.netloc or any(ch in url for ch in ['\\','\n','\r','\x00']): raise ValueError('Unsupported or malformed camera URL')
    return urlunparse((p.scheme.lower(),p.netloc,p.path,p.params,p.query,p.fragment))

def safe_url_for_log(url):
    p=urlparse(url); host=p.hostname or ''; port=f':{p.port}' if p.port else ''
    return f'{p.scheme}://{host}{port}{p.path}'
