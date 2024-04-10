# @yaml
# signature: netlify
# docstring: deploys a website within the current directory to the internet via netlify. CURRENT WORKING DIRECTORY MUST BE /usr/app for it to work.
netlify() {
    python deploy_netlify.py
}