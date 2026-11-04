# Entorno reproducible del intérprete LSP (Linux): MediaPipe, OpenCV, TensorFlow/Keras, SWI-Prolog y g++.
# En Windows, Keras no carga por la política de control de aplicaciones (ENV-03); este contenedor lo evita.
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 libegl1 libgles2 swi-prolog-nox g++ git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

ENV PYTHONUNBUFFERED=1 TF_CPP_MIN_LOG_LEVEL=2
EXPOSE 5000
CMD ["bash"]
