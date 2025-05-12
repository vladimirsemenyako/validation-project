import yaml
import argparse
import os
from pathlib import Path

from core.validator import RawValidator, SourceValidator

def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)

def parse_args():
    parser = argparse.ArgumentParser(description='Validate data files')
    parser.add_argument('--type', choices=['raw', 'source', 'both'], default='both',
                        help='Validation type: raw, source, or both')
    
    # В Docker контейнере пути будут относительно /app, иначе используем ../files
    # По умолчанию используем пути в проекте
    docker_mode = os.path.exists('/app')
    
    if docker_mode:
        default_raw_path = '/app/src/files/raw'
        default_source_path = '/app/src/files/source'
    else:
        default_raw_path = '../files/raw'
        default_source_path = '../files/source'
    
    parser.add_argument('--raw-path', default=default_raw_path,
                        help='Path to raw data files')
    parser.add_argument('--source-path', default=default_source_path,
                        help='Path to source data files')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Проверяем существование путей
    raw_path = Path(args.raw_path)
    source_path = Path(args.source_path)
    
    print(f"Paths to validate:")
    print(f"RAW path: {raw_path} (exists: {raw_path.exists()})")
    print(f"SOURCE path: {source_path} (exists: {source_path.exists()})")
    
    # Загрузка всех конфигураций
    raw_config = load_config("config/validation_rules/raw.yaml")
    source_config = load_config("config/validation_rules/source.yaml")
    
    # Выполнение валидации в зависимости от выбранного типа
    if args.type in ['raw', 'both']:
        print(f"RAW Validation was started in folder: {args.raw_path}")
        if raw_path.exists():
            raw_validator = RawValidator(raw_config)
            raw_report = raw_validator.validate(args.raw_path)
            print(f"RAW Validation report was generated: {raw_report}")
        else:
            print(f"ERROR: RAW folder does not exist: {args.raw_path}")
    
    if args.type in ['source', 'both']:
        print(f"SOURCE Validation was started in folder: {args.source_path}")
        if source_path.exists():
            source_validator = SourceValidator(source_config)
            source_report = source_validator.validate(args.source_path)
            print(f"SOURCE Validation report was generated: {source_report}")
        else:
            print(f"ERROR: SOURCE folder does not exist: {args.source_path}") 