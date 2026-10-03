#!/usr/bin/env python3
"""copilot-cli: Copilot Studio agent'ınla terminalden konuş (Direct Line v3).

Kullanım:
  setx COPILOT_SECRET "<Web channel security Secret 1>"   (Windows, bir kere)
  python copilot_cli.py                  -> sohbet modu
  python copilot_cli.py "soru"           -> tek soru, cevabı yaz, çık
  echo "metin" | python copilot_cli.py - -> stdin'den oku
Sadece Python standart kütüphanesi kullanır, pip gerekmez.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("COPILOT_DL_URL", "https://directline.botframework.com").rstrip("/") + "/v3/directline"
USER_ID = "dl_umut_cli"
POLL_INTERVAL = 0.7      # saniye
FIRST_REPLY_TIMEOUT = 120  # agent'ın ilk cevabı için bekleme
QUIET_AFTER_REPLY = 2.5    # son mesajdan sonra başka mesaj gelmezse bitir

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def die(msg):
    print(f"[hata] {msg}", file=sys.stderr)
    sys.exit(1)


class DirectLine:
    def __init__(self, secret):
        self.token = secret
        self.conv_id = None
        self.watermark = None

    def _req(self, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(BASE + path, data=data, method=method)
        req.add_header("Authorization", "Bearer " + self.token)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code in (401, 403):
                die(f"{e.code} yetkisiz. Secret yanlış ya da agent publish edilmemiş. {detail}")
            die(f"HTTP {e.code}: {detail}")
        except urllib.error.URLError as e:
            die(f"Bağlantı hatası: {e.reason}")

    def start(self):
        # Secret -> kısa ömürlü token (secret sadece burada kullanılır)
        tok = self._req("POST", "/tokens/generate", {"user": {"id": USER_ID}})
        self.token = tok.get("token", self.token)
        conv = self._req("POST", "/conversations")
        self.conv_id = conv["conversationId"]
        self.token = conv.get("token", self.token)

    def send(self, text):
        act = {"type": "message", "from": {"id": USER_ID}, "text": text, "locale": "tr-TR"}
        return self._req("POST", f"/conversations/{self.conv_id}/activities", act).get("id")

    def poll(self):
        q = f"?watermark={self.watermark}" if self.watermark else ""
        res = self._req("GET", f"/conversations/{self.conv_id}/activities{q}")
        self.watermark = res.get("watermark", self.watermark)
        return res.get("activities", [])

    def ask(self, text):
        self.send(text)
        replies, start, last = [], time.time(), None
        while True:
            for a in self.poll():
                if a.get("from", {}).get("id") == USER_ID or a.get("type") != "message":
                    continue
                replies.append(render(a))
                last = time.time()
            now = time.time()
            if last and now - last > QUIET_AFTER_REPLY:
                return replies
            if not last and now - start > FIRST_REPLY_TIMEOUT:
                return replies or ["[agent cevap vermedi - zaman aşımı]"]
            time.sleep(POLL_INTERVAL)


def render(a):
    parts = [a.get("text") or ""]
    for att in a.get("attachments") or []:
        c = att.get("content")
        if isinstance(c, dict):
            parts.append(c.get("text") or json.dumps(c, ensure_ascii=False)[:500])
        elif att.get("contentUrl"):
            parts.append(f"[ek] {att['contentUrl']}")
    for sa in (a.get("suggestedActions") or {}).get("actions", []):
        parts.append(f"  > {sa.get('title')}")
    return "\n".join(p for p in parts if p).strip()


def main():
    secret = os.environ.get("COPILOT_SECRET")
    if not secret:
        die("COPILOT_SECRET ortam değişkeni yok. Copilot Studio > Settings > Security > "
            "Web channel security > Secret 1'i kopyala, sonra: setx COPILOT_SECRET \"...\" ve yeni terminal aç.")
    dl = DirectLine(secret)
    dl.start()

    args = sys.argv[1:]
    if args:
        text = sys.stdin.read() if args == ["-"] else " ".join(args)
        print("\n\n".join(dl.ask(text)))
        return

    print("Copilot Studio CLI - çıkmak için 'exit' / Ctrl+C\n")
    while True:
        try:
            text = input("sen > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in ("exit", "quit", "çık"):
            break
        for r in dl.ask(text):
            print(f"\nagent > {r}\n")


if __name__ == "__main__":
    main()
