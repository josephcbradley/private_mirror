import subprocess
import tempfile
import os
import concurrent.futures
from threading import Lock
from tqdm import tqdm

TARGET_PLATFORMS = [
    "linux",  # Standard Linux
    "windows",  # Windows 64-bit
]

PYTHON_VERSIONS = ["3.12", "3.13", "3.14", "3.15"]

BD_TEMPLATE_PATH = "bd_template.conf"
BD_CONF_PATH = "bd.conf"

TIMEOUT = 15

# Lock for writing to failed packages file
failure_log_lock = Lock()

def get_deps(pkg: str, platform: str, pyver: str, failed_dir: str = "failed_pkgs.txt") -> list[str]:
    # Use a temporary file for requirements to avoid race conditions
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".in") as tmp:
        tmp_path = tmp.name
        tmp.write(pkg)
    
    cmd = [
        "uv", "pip", "compile", 
        "--python-platform", platform, 
        "--python-version", pyver, 
        tmp_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, check=True, timeout=TIMEOUT)
        
        decoded = result.stdout.decode("utf-8", errors="replace")
        filtered_lines = [line for line in decoded.splitlines() if "#" not in line]
        return filtered_lines

    except subprocess.TimeoutExpired:
        print(f"Dependency resolution timed out for {pkg}, {pyver}, {platform} (>{TIMEOUT}s)")
        with failure_log_lock:
            with open(failed_dir, "a") as f:
                f.write(f"{pkg},{pyver},{platform}\n")
        return []

    except Exception as e:
        print(f"No resolution found for {pkg}, {pyver}, {platform}: {e}")
        with failure_log_lock:
            with open(failed_dir, "a") as f:
                f.write(f"{pkg},{pyver},{platform}\n")
        return []
    
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def download_python_versions():
    print("Ensuring Python versions are installed...")
    for pyver in PYTHON_VERSIONS:
        try:
            subprocess.run(["uv", "python", "install", pyver], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install Python {pyver}: {e}")


if __name__ == "__main__":
    download_python_versions()

    with open("wishlist.txt", "r") as f:
        # Strip whitespace to ensure clean package names
        INPUT_PACKAGES: list[str] = [line.strip() for line in f.readlines() if line.strip()]

    complete_deps_list = []
    tasks = []

    # Prepare all tasks
    for platform in TARGET_PLATFORMS:
        for pyver in PYTHON_VERSIONS:
            for package in INPUT_PACKAGES:
                tasks.append((package, platform, pyver))

    print(f"Starting resolution for {len(tasks)} tasks...")

    # Execute tasks in parallel
    # Adjust max_workers based on system capabilities or limit if needed (e.g., max_workers=8)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_deps, pkg, plat, py) for pkg, plat, py in tasks]
        
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(tasks)):
            result = future.result()
            if result:
                complete_deps_list.extend(result)

    complete_deps_list = sorted(set(complete_deps_list))

    with open(BD_TEMPLATE_PATH, "r") as bd_template_file:
        bd_template_text = bd_template_file.read()

    bd_conf_text = bd_template_text + "\n".join(
        ["\t" + line for line in complete_deps_list]
    )

    with open(BD_CONF_PATH, "w") as outfile:
        outfile.write(bd_conf_text)

    print("Finished.")