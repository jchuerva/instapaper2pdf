# Instapaper2pdf

Based in this [script](https://gist.github.com/jaflo/8af4ebf698977c181ac9b91c1e2fa2b0)

This script download all your instapaper articles in pdf format.

## Setup

You need to set up the `INSTAPAPER_USERNAME` & `INSTAPAPER_PASSWORD` local env variables.

## Run

If you want to unclude the folders, you need to update the `CATEGORY` variable in the `main.py` file, adding each folder name and id

Then, run:

```python
python main.py
```

All your articles will be downloaded in the `/pdfs` folder