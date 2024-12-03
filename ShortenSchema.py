import sqlite3
import json
from pathlib import Path

# Paths
db_path = Path("data/sec_nport_data_combined.db")
metadata_path = Path("data/nport_metadata.json")
schema_file_path = Path("data/ShortenSchema.txt")

def load_metadata(metadata_path):
    """
    Loads metadata from the JSON file and returns a dictionary mapping column names to descriptions.
    """
    with open(metadata_path, 'r') as file:
        metadata = json.load(file)

    column_metadata = {}
    for table in metadata.get("tables", []):
        table_name = table["url"].split(".")[0].upper()  # Extract table name (e.g., "SUBMISSION")
        columns = table.get("tableSchema", {}).get("columns", [])
        column_metadata[table_name] = {
            col["name"].upper(): {
                "titles": col.get("titles", col["name"]),
                "datatype": col.get("datatype", {}).get("base", "unknown"),
                "description": col.get("dc:description", "No description available."),
            }
            for col in columns
        }
    return column_metadata

def get_table_schema(db_path, metadata, output_file):
    """
    Generates a schema for the SQLite database and writes it to a text file.
    Includes column descriptions from metadata and excludes dropped fields.
    """
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Fetch all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        with open(output_file, 'w') as f:
            for table_name, in tables:
                # Write table name and the columns it includes
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()

                # Prepare the list of column names
                column_names = [col[1] for col in columns]

                # Metadata for the current table (if any)
                table_metadata = metadata.get(table_name, {})

                # Optional: Check for 'YEAR' and 'QUARTER' columns
                if "YEAR" not in column_names:
                    column_names.append("YEAR")
                if "QUARTER" not in column_names:
                    column_names.append("QUARTER")

                # Format the output
                columns_str = ', '.join(column_names)
                f.write(f"{table_name} table includes columns {columns_str}\n")

    print(f"Schema written to {output_file}")

# Main Execution
if __name__ == "__main__":
    # Load metadata
    metadata = load_metadata(metadata_path)

    # Generate schema with metadata
    get_table_schema(db_path, metadata, schema_file_path)
