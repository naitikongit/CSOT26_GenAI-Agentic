import os


NOTES_DIR = "notes"

def ensure_notes_dir():
    if not os.path.exists(NOTES_DIR):
        os.makedirs(NOTES_DIR)

def list_files() -> dict:
    """List all research notes in the notes directory."""
    ensure_notes_dir()
    try:
        files = os.listdir(NOTES_DIR)
        if not files:
            return {"content": "No files found in notes/.", "error": None}
        return {"content": "\n".join(files), "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}

def write_file(filename: str, content: str) -> dict:
    """Write a new note to the notes directory."""
    ensure_notes_dir()
    filepath = os.path.join(NOTES_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return {"content": f"Successfully wrote to {filename}", "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}

def read_file(filename: str, start_line: int = 1, read_lines: int = 50) -> dict:
    """Read a specific file with line numbers, supporting pagination."""
    filepath = os.path.join(NOTES_DIR, filename)
    if not os.path.exists(filepath):
        return {"content": None, "error": f"File {filename} not found."}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, start_idx + read_lines)
        
        chunk = lines[start_idx:end_idx]
        has_more = end_idx < total_lines
        
        output = []
        for i, line in enumerate(chunk, start=start_idx + 1):
            output.append(f"{i:03d} | {line.rstrip()}")
            
        content_str = "\n".join(output)
        if has_more:
            content_str += f"\n... (File has {total_lines - end_idx} more lines. Use start_line={end_idx + 1} to read further)"
            
        return {"content": content_str, "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}

def edit_file(filename: str, action: str, line_number: int = -1, text: str = "") -> dict:
    """Edit a file line-by-line (append, delete, replace) and show a diff."""
    filepath = os.path.join(NOTES_DIR, filename)
    if not os.path.exists(filepath):
        return {"content": None, "error": f"File {filename} not found."}
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        diff = []
        if action == "append":
            lines.append(text + "\n")
            diff.append(f"+ {text}")
        elif action == "delete":
            idx = line_number - 1
            if 0 <= idx < len(lines):
                diff.append(f"- {lines[idx].rstrip()}")
                del lines[idx]
            else:
                return {"content": None, "error": "Line number out of range."}
        elif action == "replace":
            idx = line_number - 1
            if 0 <= idx < len(lines):
                diff.append(f"- {lines[idx].rstrip()}")
                lines[idx] = text + "\n"
                diff.append(f"+ {text}")
            else:
                return {"content": None, "error": "Line number out of range."}
        else:
            return {"content": None, "error": "Invalid action. Use 'append', 'delete', or 'replace'."}
            
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
            
        return {"content": f"Edit successful. Diff preview:\n" + "\n".join(diff), "error": None}
    except Exception as e:
        return {"content": None, "error": str(e)}