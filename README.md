![img.png](img.png)

# Get started:

After cloning, and with python 3.12 installed, run this

```bash
python3.12 -m venv venv &&
source venv/bin/activate &&
pip install -r requirements.txt &&
jupyter lab
```

You should be presented with a jupyter lab.

Open `slides/presentation.md` by right-clicking and selecting `Open with > Marp Preview`.

## Demos

- `examples/agenda_demo/` is an advanced demo. To run, install requirements, then:

```bash
uvicorn demos.agenda_demo.web_app:app --reload

```

and you should be able to access http://127.0.0.1:8000

## Tools

- `qrslide.py` is used to generate a QR code for the presentation url.