import os

# Files or folders you want to ignore
EXCLUDE = ['temp', 'logo.png', 'racing_data.db', 'racing_ledger.db', 'pack_project.py']
EXTENSIONS = ['.py', '.md', '.json', '.txt']

out_file = "full_project_codebase.txt"

with open(out_file, "w", encoding="utf-8") as f_out:
    for root, dirs, files in os.walk("."):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        
        for file in files:
            if file in EXCLUDE:
                continue
            ext = os.path.splitext(file)[1]
            if ext in EXTENSIONS:
                file_path = os.path.join(root, file)
                f_out.write(f"\n\n{'='*50}\n")
                f_out.write(f"FILE: {file_path}\n")
                f_out.write(f"{'='*50}\n\n")
                try:
                    with open(file_path, "r", encoding="utf-8") as f_in:
                        f_out.write(f_in.read())
                except Exception as e:
                    f_out.write(f"[Could not read file due to error: {e}]\n")

print(f"Project packed successfully into: {out_file}")