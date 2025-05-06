import yaml

from core.validator import RawValidator

def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    config = load_config("config/validation_rules/raw.yaml")
    validator = RawValidator(config)
    report = validator.validate("../files/raw")  # path to all source files