from pathlib import Path
import jsonref
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import ThreadMessage

class Utilities:
    @property
    def files_path(self) -> Path:
        """Return the path to the files directory."""
        return Path(__file__).parent / "files"
    
    def load_instructions(self, instructions_file: str) -> str:
        """Load instructions from a file."""
        file_path = self.files_path / instructions_file
        with file_path.open("r", encoding="utf-8", errors="ignore") as file:
            return file.read()
    
    def read_text_file(self, file_path) -> str:
        """Read a text file and return its content."""
        file_path = self.files_path / file_path
        with file_path.open("r", encoding="utf-8", errors="ignore") as file:
            return file.read()
        
    def read_json_file(self, file_path) -> dict:
        """Read a JSON file and return its content."""
        file_path = self.files_path / file_path
        with file_path.open("r", encoding="utf-8", errors="ignore") as file:
            return jsonref.load(file)

def main():
    util = Utilities()
    print(util.files_path)  # Example usage of the files_path property

    sql_definition = util.read_text_file("azure-sql-schema.sql")
    print(sql_definition)  # Example usage of the read_text_file method

if __name__ == "__main__":
    main()