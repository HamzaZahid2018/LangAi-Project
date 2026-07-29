import stanza

def setup_stanza_offline():
    print("Downloading English rules...")
    stanza.download('en')
    print("Downloading Urdu rules...")
    stanza.download('ur')
    print("Downloading Arabic rules...")
    stanza.download('ar')
    print("Downloading French rules...")
    stanza.download('fr')
    print("Downloading German rules...")
    stanza.download('de')
    print("Downloading Hindi rules...")
    stanza.download('hi')
    print("\nAll Done! Stanza Is Now Ready To Work Completely Offline.")

if __name__ == "__main__":
    setup_stanza_offline()