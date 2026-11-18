# Minimal Home Assistant client: REST calls and one-shot WebSocket commands.
# Receives the base URL and an access token; raises HaError with a code on failure.
import asyncio
import json

import httpx
import websockets


class HaError(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


class HaClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def post(self, path: str, payload: dict | None = None, form: bool = False) -> dict:
        url = f"{self.base_url}{path}"
        try:
            if form:
                resp = httpx.post(url, data=payload, headers=self._headers(), timeout=60)
            else:
                resp = httpx.post(url, json=payload or {}, headers=self._headers(), timeout=60)
        except httpx.HTTPError as exc:
            raise HaError("E_HA_DOWN", f"{url} no responde ({exc}). Arranca el stack con docker compose up -d.")
        if resp.status_code >= 400:
            raise HaError("E_HA_HTTP", f"{path} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json() if resp.content else {}

    def get(self, path: str) -> dict | list:
        try:
            resp = httpx.get(f"{self.base_url}{path}", headers=self._headers(), timeout=30)
        except httpx.HTTPError as exc:
            raise HaError("E_HA_DOWN", str(exc))
        if resp.status_code >= 400:
            raise HaError("E_HA_HTTP", f"{path} -> {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def ws(self, *commands: dict) -> list:
        """Runs WebSocket commands in order and returns their results."""
        return asyncio.run(self._ws(list(commands)))

    async def _ws(self, commands: list) -> list:
        url = self.base_url.replace("http", "ws", 1) + "/api/websocket"
        results = []
        async with websockets.connect(url, max_size=None) as sock:
            await sock.recv()
            await sock.send(json.dumps({"type": "auth", "access_token": self.token}))
            auth = json.loads(await sock.recv())
            if auth.get("type") != "auth_ok":
                raise HaError("E_HA_AUTH", "El token no es válido. Borra el archivo de secretos y repite.")
            for msg_id, cmd in enumerate(commands, start=1):
                await sock.send(json.dumps({"id": msg_id, **cmd}))
                while True:
                    reply = json.loads(await sock.recv())
                    if reply.get("id") == msg_id and reply.get("type") == "result":
                        break
                if not reply.get("success"):
                    raise HaError("E_HA_WS", f"{cmd['type']}: {reply.get('error')}")
                results.append(reply.get("result"))
        return results
