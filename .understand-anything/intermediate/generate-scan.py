import os, json, subprocess

PROJECT_ROOT = "/home/hit/ROS"

# Collect all files respecting .understandignore
# We'll use find with exclusions matching our ignore patterns
result = subprocess.run(
    ["find", PROJECT_ROOT, "-type", "f",
     "-not", "-path", "*/.git/*",
     "-not", "-path", "*/node_modules/*",
     "-not", "-path", "*/__pycache__/*",
     "-not", "-path", "*/build/*",
     "-not", "-path", "*/install/*",
     "-not", "-path", "*/log/*",
     "-not", "-path", "*/.understand-anything/*",
     "-not", "-path", "*/.omo/*",
     "-not", "-path", "*/.ralph/*",
     "-not", "-path", "*/.codex/*",
     "-not", "-path", "*/worktree/*",
     "-not", "-path", "*/.pytest_cache/*",
     "-not", "-path", "*/.claude/*",
     "-not", "-path", "*/.vscode/*",
     "-not", "-path", "*/src/data_clean/*",
     "-not", "-path", "*/src/data_collection/*",
     "-not", "-path", "*/DOCS/*",
     "-not", "-path", "*/asset/*",
     "-not", "-path", "*/third_party/*",
     "-not", "-path", "*/.agents/*",
     "-not", "-name", "*.pyc",
     ],
    capture_output=True, text=True
)

files = sorted(result.stdout.strip().split("\n"))

# Categorize files
def get_file_category(path, lang):
    ext = os.path.splitext(path)[1].lower()
    rel = os.path.relpath(path, PROJECT_ROOT)
    
    if ext in ('.py', '.sh', '.js', '.ts', '.go', '.rs', '.java', '.c', '.cpp'):
        return 'code'
    elif ext in ('.yaml', '.yml', '.json', '.toml', '.cfg', '.ini', '.env', '.rules'):
        return 'config'
    elif ext in ('.md', '.rst', '.txt', '.mdx'):
        return 'docs'
    elif ext in ('.launch.py',):
        return 'infra'
    elif ext in ('.xml', '.proto', '.sql', '.graphql'):
        return 'data'
    elif ext in ('.yaml',) and 'config' in rel:
        return 'config'
    else:
        return 'code'

def get_language(path):
    ext = os.path.splitext(path)[1].lower()
    lang_map = {
        '.py': 'python',
        '.sh': 'shell',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.md': 'markdown',
        '.mdx': 'markdown',
        '.txt': 'text',
        '.toml': 'toml',
        '.rules': 'udev',
        '.launch.py': 'python',
    }
    return lang_map.get(ext, 'unknown')

def count_lines(path):
    try:
        with open(path, 'r', errors='ignore') as f:
            return sum(1 for _ in f)
    except:
        return 0

# Build file list with metadata
file_entries = []
total_lines = 0
for f in files:
    if not f.strip():
        continue
    rel = os.path.relpath(f, PROJECT_ROOT)
    lang = get_language(f)
    cat = get_file_category(f, lang)
    lines = count_lines(f)
    total_lines += lines
    file_entries.append({
        "path": rel,
        "language": lang,
        "sizeLines": lines,
        "fileCategory": cat
    })

# Build import map (simplified - project-internal imports)
import_map = {}
for entry in file_entries:
    if entry["language"] == "python":
        import_map[entry["path"]] = []  # Will be populated by compute-batches

# Language counts
lang_counts = {}
for e in file_entries:
    lang_counts[e["language"]] = lang_counts.get(e["language"], 0) + 1

# Category counts
cat_counts = {}
for e in file_entries:
    cat_counts[e["fileCategory"]] = cat_counts.get(e["fileCategory"], 0) + 1

scan_result = {
    "projectName": "pi05",
    "projectDescription": "PI0.5 VLA (Vision-Language-Action) robotics package for model deployment, training, and inference on Octopus robot",
    "languages": sorted(lang_counts.keys()),
    "frameworks": ["ROS2", "PyTorch", "LeRobot"],
    "files": file_entries,
    "complexity": "moderate",
    "totalFiles": len(file_entries),
    "totalLines": total_lines,
    "languageCounts": lang_counts,
    "categoryCounts": cat_counts,
    "importMap": import_map,
    "filteredByIgnore": 0
}

with open(os.path.join(PROJECT_ROOT, ".understand-anything/intermediate/scan-result.json"), "w") as f:
    json.dump(scan_result, f, indent=2)

print(f"Scan complete: {len(file_entries)} files, {total_lines} lines")
print(f"Languages: {lang_counts}")
print(f"Categories: {cat_counts}")
