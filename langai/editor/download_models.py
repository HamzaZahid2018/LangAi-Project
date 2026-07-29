import glob
import os
import argostranslate.package

def _install_local_argos_models(local_dir: str = 'offline_models'):
    model_pattern = os.path.join(local_dir, '*.argosmodel')
    model_files = sorted(glob.glob(model_pattern))

    if not model_files:
        print(f"No local model files found in: {os.path.abspath(local_dir)}")
        print("Add .argosmodel files there, then run this script again.")
        return
    print(f"Found {len(model_files)} local model file(s). Installing...")
    for model_path in model_files:
        try:
            print(f"Installing: {os.path.basename(model_path)}")
            argostranslate.package.install_from_path(model_path)
            print("Installed successfully.\n")
        except Exception as e:
            print(f"Failed to install {model_path}: {e}\n")
def download_offline_models(local_dir: str = 'offline_models'):
    print("Updating package index...")
    try:
        argostranslate.package.update_package_index()
    except Exception as e:
        print(f"Could not reach online package index: {e}")
        print("Falling back to local .argosmodel installation.")
        _install_local_argos_models(local_dir=local_dir)
        return
    available_packages = argostranslate.package.get_available_packages()
    target_languages = ['fr', 'ur', 'en', 'de', 'hi', 'ar'] 
    for target in target_languages:
        print(f"Looking for English to {target.upper()} model...")
        package_to_install = next(
            filter(lambda x: x.from_code == 'en' and x.to_code == target, available_packages), 
            None
        )

        if package_to_install:
            print(f"Downloading and installing: {package_to_install}...")
            argostranslate.package.install_from_path(package_to_install.download())
            print(f"Success! English to {target.upper()} is ready for offline use.\n")
        else:
            print(f"Could not find an offline model for en -> {target}.\n")

    print("All done! You Can Now Use Offline Translation.")

if __name__ == "__main__":
    download_offline_models()