import os

from netlify_py import NetlifyPy
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    os.chdir("..")
    API_KEY = os.environ["NETLIFY_AUTH_TOKEN"]
    SITE_ID = os.environ["NETLIFY_SITE_ID"]
    n = NetlifyPy(access_token=API_KEY)
    new_deploy = n.deploys.deploy_site(
        SITE_ID,
        "app"
    )
    os.chdir("./app")
    print(new_deploy)