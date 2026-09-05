# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# robynpy (Marketing Mix Modeling) depends on rpy2 for R interop, and rpy2 needs an actual
# R install to even *build* its wheel (not just to run) -- `pip install` fails outright
# without it. build-essential is for rpy2's C extension.
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

COPY . .

EXPOSE 8888

# Container-local Jupyter for opening/running the notebooks without a local Python install.
# No token/password: only reachable via the port mapping on your own machine, same trust
# boundary as running `jupyter notebook` locally.
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", \
     "--NotebookApp.token=", "--NotebookApp.password="]
