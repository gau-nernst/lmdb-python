import json
import urllib.request

index_template = "<!DOCTYPE html>\n<html>\n<body>\n{}\n</body>\n</html>\n"


def update_index(url: str, save_path: str):
    files = []
    with urllib.request.urlopen(url) as resp:
        releases = json.load(resp)

    for release in releases:
        for asset in release["assets"]:
            wheel_url = asset["browser_download_url"]
            wheel_name = asset["name"]
            files.append(f'    <a href="{wheel_url}">{wheel_name}</a>')

    with open(save_path, "w") as f:
        f.write(index_template.format("\n".join(files)))


if __name__ == "__main__":
    url = "https://api.github.com/repos/gau-nernst/lmdb-python/releases"
    index_path = "docs/index.html"
    update_index(url, index_path)
