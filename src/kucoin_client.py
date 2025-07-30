import base64
import hmac
import hashlib
import time
import requests

class KucoinClient:
    def __init__(self, key: str, secret: str, passphrase: str, base_url: str):
        self.key = key
        self.secret = secret
        self.passphrase = passphrase
        self.base_url = base_url.rstrip('/')

    def _sign(self, method: str, endpoint: str, body: str = '') -> dict:
        now = int(time.time() * 1000)
        str_to_sign = f"{now}{method.upper()}{endpoint}{body}"
        signature = base64.b64encode(
            hmac.new(self.secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest()
        )
        passphrase = base64.b64encode(
            hmac.new(self.secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest()
        )
        return {
            'KC-API-KEY': self.key,
            'KC-API-KEY-VERSION': '2',
            'KC-API-SIGN': signature.decode(),
            'KC-API-TIMESTAMP': str(now),
            'KC-API-PASSPHRASE': passphrase.decode(),
            'Content-Type': 'application/json'
        }

    def place_order(self, symbol: str, side: str, size: float, price: float) -> dict:
        endpoint = '/api/v1/orders'
        body = {
            'symbol': symbol,
            'side': side,
            'size': size,
            'price': price,
            'type': 'limit'
        }
        import json
        body_json = json.dumps(body)
        headers = self._sign('POST', endpoint, body_json)
        resp = requests.post(self.base_url + endpoint, headers=headers, data=body_json)
        resp.raise_for_status()
        return resp.json()
