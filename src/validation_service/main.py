import yaml
import argparse

from core.validator import RawValidator, SourceValidator

def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

def parse_args():
    parser = argparse.ArgumentParser(description='Validate data files')
    parser.add_argument('--type', choices=['raw', 'source', 'both'], default='both',
                        help='Validation type: raw, source, or both')
    parser.add_argument('--raw-path', default='../files/raw',
                        help='Path to raw data files')
    parser.add_argument('--source-path', default='../files/source',
                        help='Path to source data files')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    raw_config = load_config("config/validation_rules/raw.yaml")
    source_config = load_config("config/validation_rules/source.yaml")

    if args.type in ['raw', 'both']:
        print(f"RAW Validation was started in folder: {args.raw_path}")
        raw_validator = RawValidator(raw_config)
        raw_report = raw_validator.validate(args.raw_path)
        print(f"RAW Validation report was generated: {raw_report}")
    
    if args.type in ['source', 'both']:
        print(f"SOURCE Validation was started in folder: {args.source_path}")
        source_validator = SourceValidator(source_config)
        source_report = source_validator.validate(args.source_path)
        print(f"SOURCE Validation report was generated: {source_report}")