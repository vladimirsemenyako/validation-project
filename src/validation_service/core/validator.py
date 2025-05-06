from pathlib import Path
import pandas as pd
from typing import List, Dict
import csv
from datetime import datetime


class RawValidator:
    def __init__(self, config: Dict):
        self.config = config["raw"]
        self.errors: List[Dict] = []

    def validate(self, base_path: str) -> str:
        base_path = Path(base_path)
        self._check_folders(base_path)
        self._check_files(base_path)
        
        # for filenaming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"validation_report_{timestamp}.csv"

        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['error_level', 'error_text', 'file_name', 'folder_name', 'line_number']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for error in self.errors:
                writer.writerow(error)
        
        return output_file

    def _check_folders(self, base_path: Path):
        for folder in self.config["required_folders"]:
            folder_path = base_path / folder
            if not folder_path.exists():
                self.errors.append({
                    'error_level': 'error',
                    'error_text': f"Required folder '{folder}' is missing",
                    'file_name': '',
                    'folder_name': str(folder_path),
                    'line_number': ''
                })
            elif not any(folder_path.iterdir()):
                self.errors.append({
                    'error_level': 'warning',
                    'error_text': f"Folder '{folder}' does not contain any file",
                    'file_name': '',
                    'folder_name': str(folder_path),
                    'line_number': ''
                })

    def _check_files(self, base_path: Path):
        for folder, requirements in self.config["file_requirements"].items():
            folder_path = base_path / folder

            if not folder_path.exists():
                continue

            for file_path in folder_path.iterdir():
                if file_path.is_file():
                    self._validate_columns(
                        file_path=file_path,
                        required_columns=requirements["required_columns"]
                    )

    def _validate_columns(self, file_path: Path, required_columns: List[str]):
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path, nrows=0)
            else:
                self.errors.append({
                    'error_level': 'error',
                    'error_text': f"Unsupported file format: {file_path}",
                    'file_name': file_path.name,
                    'folder_name': str(file_path.parent),
                    'line_number': ''
                })
                return

            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                for col in missing:
                    self.errors.append({
                        'error_level': 'error',
                        'error_text': f"Required column '{col}' is missing",
                        'file_name': file_path.name,
                        'folder_name': str(file_path.parent),
                        'line_number': ''
                    })

        except Exception as e:
            self.errors.append({
                'error_level': 'error',
                'error_text': f"Failed to read {file_path}: {str(e)}",
                'file_name': file_path.name,
                'folder_name': str(file_path.parent),
                'line_number': ''
            })