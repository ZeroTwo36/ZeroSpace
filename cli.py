import os
import toml
from typer import Typer
import requests
import typer

app = Typer()


@app.command()
def login(username:str="guest",password:str="12345"):
    with open("config.toml","w") as f:
        toml.dump({"usernames":username,"passwords":password},f)
    print("Stored LOGIN Credentials!")

@app.command()
def push(container:str,filename:str):
    if os.path.exists(filename):
        print("Connecting to ZeroSpace...")
        logins = toml.load(open("config.toml"))
        print("Pushing to upstream...")
        resource = requests.get(f'http://192.168.68.115/dockerlang.up',headers={
            "username":logins["usernames"],
            "password":logins["passwords"],
            "container":container.replace(" ","-").lower(),
        },files={"main":open(filename,"rb")})
        print("Received Response:")
        print(resource.text)
        print(resource.json()["result"])


@app.command()
def pull(container:str,filename:str):
        print("Connecting to ZeroSpace...")
        logins = toml.load(open("config.toml"))
        print("Pushing to upstream...")
        resource = requests.get(f'http://192.168.68.115/dockerlang.down',headers={
            "username":logins["usernames"],
            "password":logins["passwords"],
            "container":container.replace(" ","-").lower(),
            "filename":filename
        })
        with open(filename,"wb") as f:
            f.write(resource.content)
        print("Received Response:")
        print(resource.text)
        print(resource.json()["result"])


@app.command()
def init():
    print("Let's create your Server!")
    imgname = input("Server Name (myAwesomeServer) : ") or "myAwesomeServer"
    imgtype = input("Server Image (ubuntu:16.04) : ") or "ubuntu:16.04"
    entry = input("Entry Point (tail /dev/null) : ") or 'tail /dev/null'
    logins = toml.load(open("config.toml"))
    resource = requests.get(f'http://192.168.68.115/dockerlang.init',headers={
            "username":logins["usernames"],
            "password":logins["passwords"],
            "container-img":imgtype,
            "container-name":imgname.replace(" ","-").lower(),
            "container-entry-cmd":entry,
        })
    container = imgname.replace(" ","-").lower()
    print(f"Tagged {container}, received Response {resource.json().get('result')}")
    print("Copying System Files...")
    _push("help.sh",container)
    print(_E(container,"sh ./help.sh"))
    
def _push(filename,container):    
    if os.path.exists(filename):
        logins = toml.load(open("config.toml"))
        resource = requests.get(f'http://192.168.68.115/dockerlang.up',headers={
            "username":logins["usernames"],
            "password":logins["passwords"],
            "container":container.replace(" ","-").lower(),
        },files={"main":open(filename,"rb")})

def _E(container,cmd):
    logins = toml.load(open("config.toml"))
    resource = requests.get(f'http://192.168.68.115/dockerlang.communicate',headers={
            "username":logins["usernames"],
            "password":logins["passwords"],
            "container":container.replace(" ","-").lower(),
            "cmd":cmd,
        }).json()
    return resource["result"]

@app.command()
def rm(container):
    res = input(f"Do you REALLY wish to remove {container}? Press Y for yes or any other key for no > ")
    if res.lower() == "y":
        logins = toml.load(open("config.toml"))
        print(f"Removing {container}, this can take a while...")
        resource = requests.get(f'http://192.168.68.115/dockerlang.rm',headers={
                "username":logins["usernames"],
                "password":logins["passwords"],
                "container":container.replace(" ","-").lower(),
            }).json()
        print(resource.get("result"))
    else:
        print("Cancelled!")
        


@app.command()
def run(container,*,cmd=None):
    print("Posting to upstream Server...")
    logins = toml.load(open("config.toml"))
    if cmd:
        resource = requests.get(f'http://192.168.68.115/dockerlang.communicate',headers={
                "username":logins["usernames"],
                "password":logins["passwords"],
                "container":container.replace(" ","-").lower(),
                "cmd":cmd,
            }).json()
        print(resource["result"])
    else:
        while cmd != "exit":
            cmd = input(f"{container}> ")
            if cmd == "exit":
                break
                
            resource = requests.get(f'http://192.168.68.115/dockerlang.communicate',headers={
                    "username":logins["usernames"],
                    "password":logins["passwords"],
                    "container":container.replace(" ","-").lower(),
                    "cmd":cmd,
                })
            print(resource.json().get("result"))

app()
