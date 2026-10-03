# copilot-cli

Copilot Studio agent'ınla **terminalden** konuş. Direct Line v3 API kullanır, sadece Python standart kütüphanesi (pip yok).

## Kurulum (Windows)
1. Copilot Studio → agent'ını **Publish** et.
2. **Settings → Security → Web channel security** → **Secret 1**'i kopyala.
3. PowerShell:
   ```powershell
   setx COPILOT_SECRET "BURAYA_SECRET"
   ```
   Yeni bir terminal aç.
4. Çalıştır:
   ```powershell
   python copilot_cli.py                 # sohbet modu
   python copilot_cli.py "bugün ne yapsam" # tek soru
   Get-Content not.txt | python copilot_cli.py -   # dosyadan
   ```

## Ayarlar
| Değişken | Açıklama |
|---|---|
| `COPILOT_SECRET` | Web channel security secret (zorunlu) |
| `COPILOT_DL_URL` | Bölgesel endpoint, ör. `https://europe.directline.botframework.com` (opsiyonel) |

## Güvenlik
- Secret'ı **asla** koda/commit'e koyma; sadece ortam değişkeni.
- Script secret'ı yalnızca kısa ömürlü token almak için kullanır.
- Secret sızarsa Copilot Studio'dan yeniden oluştur (regenerate).

## Sorun giderme
- **401/403** → secret yanlış veya agent publish edilmemiş.
- **Cevap yok / zaman aşımı** → agent yeni (GitHub Copilot harness) deneyimdeyse Direct Line desteklenmeyebilir; klasik agent kullan.
