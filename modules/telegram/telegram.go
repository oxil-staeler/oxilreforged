// modules/telegram/telegram.go
package telegram

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
)

type TelegramMessage struct {
	ChatID    string `json:"chat_id"`
	Text      string `json:"text"`
	ParseMode string `json:"parse_mode,omitempty"` // "MarkdownV2" veya "HTML" için
}

func SendToTelegram(botToken, chatID, message string) error {
	url := fmt.Sprintf("https://api.telegram.org/bot%s/sendMessage", botToken)

	msg := TelegramMessage{
		ChatID:    chatID,
		Text:      message,
		ParseMode: "MarkdownV2", // Ýstersen "HTML" yap veya kaldýr
	}

	jsonData, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	resp, err := http.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("Telegram API error: %d", resp.StatusCode)
	}

	return nil
}