from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional, Union
import csv
from datetime import datetime
from abc import ABC, abstractmethod


class BaseValidator(ABC):
    def __init__(self, config: Dict):
        self.config = config
        self.errors: List[Dict] = []

    @abstractmethod
    def validate(self, base_path: str) -> str:
        pass

    def _check_folders(self, base_path: Path, required_folders: List[str]):
        for folder in required_folders:
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

    def _generate_report(self, base_path: Path, prefix: str = "validation_report") -> str:
        report_dir = base_path / "validation_report"
        report_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"{prefix}_{timestamp}.csv"
        
        output_path = report_dir / output_file

        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = ['error_level', 'error_text', 'file_name', 'folder_name', 'line_number']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for error in self.errors:
                writer.writerow(error)
        
        return str(output_path)


class RawValidator(BaseValidator):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.raw_config = config["raw"]

    def validate(self, base_path: str) -> str:
        base_path = Path(base_path)
        self._check_folders(base_path, self.raw_config["required_folders"])
        self._check_files(base_path)
        
        return self._generate_report(base_path, prefix="raw_validation_report")

    def _check_files(self, base_path: Path):
        for folder, requirements in self.raw_config["file_requirements"].items():
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
                df = pd.read_csv(file_path)
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
            
            # Continue validation for existing columns even if some are missing
            existing_columns = [col for col in required_columns if col in df.columns]
            self._validate_data_quality(df, existing_columns, file_path)

        except Exception as e:
            self.errors.append({
                'error_level': 'error',
                'error_text': f"Failed to read {file_path}: {str(e)}",
                'file_name': file_path.name,
                'folder_name': str(file_path.parent),
                'line_number': ''
            })

    def _validate_data_quality(self, df: pd.DataFrame, columns: List[str], file_path: Path):
        """Perform basic data quality checks on existing columns"""
        for column in columns:
            if column not in df.columns:
                continue
                
            for idx, value in enumerate(df[column], start=2):  # start=2 because CSV has header
                # Check for empty/null values
                if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                    self.errors.append({
                        'error_level': 'warning',
                        'error_text': f"Empty or null value found in column '{column}'",
                        'file_name': file_path.name,
                        'folder_name': str(file_path.parent),
                        'line_number': str(idx)
                    })
                    continue
                
                # Basic data type inference and validation
                if column.lower() in ['id', 'order_id', 'customer_id', 'fruit_id']:
                    # Should be numeric for ID columns
                    try:
                        str_value = str(value).strip()
                        if '.' in str_value:
                            self.errors.append({
                                'error_level': 'error',
                                'error_text': f"ID column '{column}' contains decimal value: {value}",
                                'file_name': file_path.name,
                                'folder_name': str(file_path.parent),
                                'line_number': str(idx)
                            })
                        else:
                            int(str_value)
                    except (ValueError, TypeError):
                        self.errors.append({
                            'error_level': 'error',
                            'error_text': f"ID column '{column}' contains non-numeric value: {value}",
                            'file_name': file_path.name,
                            'folder_name': str(file_path.parent),
                            'line_number': str(idx)
                        })
                
                elif column.lower() in ['date', 'created_at', 'updated_at']:
                    # Should be valid date format
                    try:
                        pd.to_datetime(value)
                    except (ValueError, TypeError):
                        self.errors.append({
                            'error_level': 'error',
                            'error_text': f"Date column '{column}' contains invalid date: {value}",
                            'file_name': file_path.name,
                            'folder_name': str(file_path.parent),
                            'line_number': str(idx)
                        })
                
                elif column.lower() in ['quantity', 'price', 'amount', 'gdp', 'grade']:
                    # Should be numeric
                    try:
                        pd.to_numeric(value)
                    except (ValueError, TypeError):
                        self.errors.append({
                            'error_level': 'error',
                            'error_text': f"Numeric column '{column}' contains non-numeric value: {value}",
                            'file_name': file_path.name,
                            'folder_name': str(file_path.parent),
                            'line_number': str(idx)
                        })


class SourceValidator(BaseValidator):
    def __init__(self, config: Dict):
        super().__init__(config)
        self.source_config = config["source"]

    def validate(self, base_path: str) -> str:
        base_path = Path(base_path)
        self._check_folders(base_path, self.source_config["required_folders"])
        self._check_files(base_path)
        
        return self._generate_report(base_path, prefix="source_validation_report")

    def _check_files(self, base_path: Path):
        for folder, file_requirements in self.source_config["folder_file_requirements"].items():
            folder_path = base_path / folder

            if not folder_path.exists():
                continue

            # Check for expected files
            for file_name, requirements in file_requirements.items():
                file_path = folder_path / file_name
                
                if not file_path.exists():
                    self.errors.append({
                        'error_level': 'error',
                        'error_text': f"Required file '{file_name}' is missing",
                        'file_name': file_name,
                        'folder_name': str(folder_path),
                        'line_number': ''
                    })
                    continue
                
                self._validate_file_schema(
                    file_path=file_path,
                    required_columns=requirements["columns"]
                )

    def _validate_file_schema(self, file_path: Path, required_columns: Dict[str, Dict[str, Any]]):
        try:
            if file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            else:
                self.errors.append({
                    'error_level': 'error',
                    'error_text': f"Unsupported file format: {file_path}",
                    'file_name': file_path.name,
                    'folder_name': str(file_path.parent),
                    'line_number': ''
                })
                return

            # Check if all required columns exist
            missing = [col for col in required_columns.keys() if col not in df.columns]
            if missing:
                for col in missing:
                    self.errors.append({
                        'error_level': 'error',
                        'error_text': f"Required column '{col}' is missing",
                        'file_name': file_path.name,
                        'folder_name': str(file_path.parent),
                        'line_number': ''
                    })

            extra = [col for col in df.columns if col not in required_columns.keys()]
            if extra:
                for col in extra:
                    self.errors.append({
                        'error_level': 'warning',
                        'error_text': f"Unexpected column '{col}' found",
                        'file_name': file_path.name,
                        'folder_name': str(file_path.parent),
                        'line_number': ''
                    })

            # Only validate columns that exist in the dataframe
            for column, requirements in required_columns.items():
                if column in df.columns:
                    expected_type = requirements["type"]
                    nullable = requirements.get("nullable", False)
                    self._validate_column_type(df, column, expected_type, file_path, nullable)

        except Exception as e:
            self.errors.append({
                'error_level': 'error',
                'error_text': f"Failed to read {file_path}: {str(e)}",
                'file_name': file_path.name,
                'folder_name': str(file_path.parent),
                'line_number': ''
            })

    def _validate_column_type(self, df: pd.DataFrame, column: str, expected_type: str, file_path: Path, nullable: bool = False):
        try:
            for idx, value in enumerate(df[column], start=2):  # start=2 because CSV has header
                # Check for NULL values
                if pd.isna(value):
                    if not nullable:
                        self.errors.append({
                            'error_level': 'error',
                            'error_text': f"NULL value not allowed for the column {column}",
                            'file_name': file_path.name,
                            'folder_name': str(file_path.parent),
                            'line_number': str(idx)
                        })
                    continue

                if expected_type == "int":
                    try:
                        # Convert to string first to handle various input types
                        str_value = str(value).strip()
                        # Check if it's a valid integer (no decimal point)
                        if '.' in str_value:
                            raise ValueError("Contains decimal point")
                        # Try to convert to int
                        int(str_value)
                    except (ValueError, TypeError):
                        self.errors.append({
                            'error_level': 'error',
                            'error_text': f"Wrong datatype for the column {column}",
                            'file_name': file_path.name,
                            'folder_name': str(file_path.parent),
                            'line_number': str(idx)
                        })
                
                elif expected_type == "float":
                    try:
                        pd.to_numeric(value)
                    except (ValueError, TypeError):
                        self.errors.append({
                            'error_level': 'error',
                            'error_text': f"Wrong datatype for the column {column}",
                            'file_name': file_path.name,
                            'folder_name': str(file_path.parent),
                            'line_number': str(idx)
                        })
                
                elif expected_type == "datetime":
                    try:
                        pd.to_datetime(value)
                    except (ValueError, TypeError):
                        self.errors.append({
                            'error_level': 'error',
                            'error_text': f"Wrong datatype for the column {column}",
                            'file_name': file_path.name,
                            'folder_name': str(file_path.parent),
                            'line_number': str(idx)
                        })
                
                elif expected_type == "str":
                    pass
                
                else:
                    self.errors.append({
                        'error_level': 'error',
                        'error_text': f"Unsupported data type '{expected_type}' for column {column}",
                        'file_name': file_path.name,
                        'folder_name': str(file_path.parent),
                        'line_number': ''
                    })

        except Exception as e:
            self.errors.append({
                'error_level': 'error',
                'error_text': f"Error validating column {column}: {str(e)}",
                'file_name': file_path.name,
                'folder_name': str(file_path.parent),
                'line_number': ''
            })