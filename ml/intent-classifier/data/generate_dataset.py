"""Regenerate the deterministic v0.3 synthetic intent dataset."""

from aegisbank_intent_classifier.dataset import write_dataset

if __name__ == "__main__":
    manifest = write_dataset()
    print(f"Generated {manifest['record_count']} records")
    print(f"SHA256={manifest['sha256']}")
