# Beer League Defense Draft

A tiny Streamlit app that runs a Monte Carlo simulation to pick which forwards have to play defense tonight.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then enter seven forwards, choose the number of defense spots, and run the draft.

## Share it temporarily

While the Streamlit app is running locally, create a public temporary link with:

```bash
npx --yes cloudflared tunnel --url http://localhost:8501
```

Copy the `trycloudflare.com` URL that command prints. The link works while your computer, the Streamlit app, and the tunnel process stay running.
