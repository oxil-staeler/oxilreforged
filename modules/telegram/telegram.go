package telegram

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
)

func SendTextToTelegram(botToken, chatID, text string) error {
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
		return fmt.Errorf("sendMessage failed: %d", resp.StatusCode)
	}
	return nil
}

func SendZipToTelegram(botToken, chatID, caption, zipPath string) error {
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
		return fmt.Errorf("sendDocument failed: %d", resp.StatusCode)
	}

	return nil
}
