[![](https://dcbadge.vercel.app/api/server/nbY6njCuxh)](https://discord.gg/nbY6njCuxh)

# 🤖 Anterion Agent

## 📖 What is Anterion?

Anterion is an open-source AI software engineer.

Anterion extends the capabilities of `SWE-agent` to plan and execute open-ended engineering tasks, with a frontend inspired by
`OpenDevin`.

We've equiped Anterion with easy deployment and UI to allow you to fix bugs and prototype ideas at ease.

## 🏁 Getting Started

🎉 Get on board with Anterion by doing the following! 🎉

### Prerequisites
* Linux, Mac OS, or [WSL on Windows](https://learn.microsoft.com/en-us/windows/wsl/install)
* [Docker](https://docs.docker.com/engine/install/)
* [Python](https://www.python.org/downloads/) >= 3.11
* [NodeJS](https://nodejs.org/en/download/package-manager) >= 18.17.1
* [Miniconda](https://docs.anaconda.com/free/miniconda/miniconda-install/)

You will need to setup all three components of the system before being able to run it:

### 1. `OpenDevin` Setup

To setup OpenDevin, run the following command:

```bash
make build-open-devin
```

### 2. `SWE-agent` Setup

Next you will need to setup the `SWE-agent`.

To start, you will need to `cd` to the `SWE-agent` directory, and run the following
command:

```bash
cd SWE-agent
conda env create -f environment.yml
conda activate swe-agent
cd ..
```

You will need to create a file called `keys.cfg` inside of the `SWE-agent`
directory:

```bash
OPENAI_API_KEY: '<OPENAI_API_KEY_GOES_HERE>'
ANTHROPIC_API_KEY: '<ANTHROPIC_API_KEY_GOES_HERE>'
GITHUB_TOKEN: '<GITHUB_PERSONAL_ACCESS_TOKEN_GOES_HERE>'
```

(Optionally) If you want to be able to use Netlify deployments, add the following
`.env` file inside of the `SWE-agent` directory:

```bash
NETLIFY_AUTH_TOKEN="<NETLIFY_AUTH_TOKEN_GOES_HERE>"
NETLIFY_SITE_ID="<NETLIFY_SITE_ID_GOES_HERE>"
```

Finally, run the following command to setup `SWE-agent`

```bash
make build-swe-agent
```

### 3. `microservice` Setup

Finally you need to setup the `microservice`, which ties together the
`OpenDevin` frontend and the `SWE-agent` agent.

```bash
make build-microservice
```

### Usage

To run Anterior, you need to run the frontend and the backend.
Run the following command to run both together:

```bash
(make run-frontend) & (make run-backend)
```

If that isn't working for some reason, run both of them separately:

```bash
make run-frontend
```

```bash
make run-backend
```

## 🙏 Special Thanks!

We'd like to say thanks to these amazing repos for inspiration!
- [OpenDevin](https://github.com/OpenDevin/OpenDevin)
- [SWE-agent](https://github.com/princeton-nlp/SWE-agent)