import subprocess
import yaml
with open("repos.yaml", "r") as file:
    data = yaml.safe_load(file)
    for repo, conf in data.items():
        remote_name, branch = conf["target"].split(" ")
        remote = conf["remotes"][remote_name]
        cmd = f"git submodule add --depth 1 -b {branch} {remote} {repo}"
        subprocess.run(cmd, shell=True)
