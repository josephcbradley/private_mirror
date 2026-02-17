import subprocess
from tqdm import tqdm

TARGET_PLATFORMS = [
    "linux",  # Standard Linux
    "windows",  # Windows 64-bit
]

PYTHON_VERSIONS = ["3.12", "3.13", "3.14", "3.15"]

BD_TEMPLATE_PATH = "bd_template.conf"
BD_CONF_PATH = "bd.conf"


def get_deps(pkg, platform, pyver, failed_dir: str = "failed_pkgs.txt") -> list[str]:
    reqs_in_path = "requirements.in"
    with open(reqs_in_path, "w") as f:
        f.write(package)
    cmd = f"uv pip compile --python-platform {platform} --python-version {pyver} requirements.in".rsplit(
        " "
    )

    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except Exception as e:
        print(f"No resolution found for {pkg}, {pyver}, {platform}: {e}")
        with open(failed_dir, "a") as f:
            f.write(f"{pkg},{pyver},{platform}\n")
        return None

    decoded = result.stdout.decode("utf-8", errors="replace")
    filtered_lines = [line for line in decoded.splitlines() if "#" not in line]

    return filtered_lines


if __name__ == "__main__":
    with open("wishlist.txt", "r") as f:
        INPUT_PACKAGES: list[str] = f.readlines()

    complete_deps_list = []
    for platform in TARGET_PLATFORMS:
        for pyver in PYTHON_VERSIONS:
            print(f"Beginning resolution for {platform} {pyver}:")
            for package in tqdm(INPUT_PACKAGES):
                new_lines = get_deps(package, platform, pyver)
                if new_lines:
                    complete_deps_list.extend(new_lines)

    complete_deps_list = list(set(complete_deps_list))

    with open(BD_TEMPLATE_PATH, "r") as bd_template_file:
        bd_template_text = bd_template_file.read()

    bd_conf_text = bd_template_text + "\n".join(
        ["\t" + line for line in complete_deps_list]
    )

    with open(BD_CONF_PATH, "w") as outfile:
        outfile.write(bd_conf_text)

    print("Finished.")
