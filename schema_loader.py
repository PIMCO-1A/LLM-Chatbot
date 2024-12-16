# schema_loader.py
def load_schema(schema_file):
    """
    Parses the schema file to extract table and column details.
    Returns a dictionary where keys are table names and values are lists of column names.
    """
    schema = {}
    current_table = None

    with open(schema_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("Table:"):
                # Extract the table name after 'Table:'
                current_table = line[len("Table:"):].strip()
                schema[current_table] = []
            elif line.startswith('-') and current_table:
                # Extract the column name before '('
                column = line.split('(')[0].replace('-', '').strip()
                schema[current_table].append(column)
    return schema
