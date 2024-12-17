import sqlite3
import json
from pathlib import Path

# Paths
db_path = Path("data/sec_nport_data_combined.db")
metadata_path = Path("data/nport_metadata.json")
schema_file_path = Path("data/data_schema.txt")


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
                f.write(f"Table: {table_name}\n")

                # Fetch column details for the table
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()

                # Metadata for the current table
                table_metadata = metadata.get(table_name, {})

                for col in columns:
                    column_name = col[1]
                    data_type = col[2]
                    notnull = bool(col[3])
                    primary_key = bool(col[5])

                    # Get metadata description
                    col_metadata = table_metadata.get(column_name.upper(), {})
                    title = col_metadata.get("titles", column_name)
                    description = col_metadata.get("description", "No description available.")

                    # Format the column details
                    column_details = f"    -{column_name}({data_type}) : {description}"
                    if primary_key:
                        column_details += " [Primary Key]"
                    elif notnull:
                        column_details += " [Not NULL]"

                    f.write(column_details + "\n")

                # Always include YEAR and QUARTER fields
                if "YEAR" not in [col[1] for col in columns]:
                    f.write("    -YEAR(INTEGER) : Reporting year\n")
                if "QUARTER" not in [col[1] for col in columns]:
                    f.write("    -QUARTER(INTEGER) : Reporting quarter\n")

                f.write("\n")  # Separate tables with a newline

    print(f"Schema written to {output_file}")


# Main Execution
if __name__ == "__main__":
    # Load metadata
    metadata = load_metadata(metadata_path)

    # Generate schema with metadata
    get_table_schema(db_path, metadata, schema_file_path)
