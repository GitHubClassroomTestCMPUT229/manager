import requests

def main():
    token = open("travis.token", "r").read().strip()
    payload = {"github_token":token}
    r = requests.post("https://api.travis-ci.org/auth/github/", data=payload)
    print(r)

if __name__ == "__main__":
    main()
