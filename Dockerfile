# Dockerfile to run kijiji reposter headless
from python:3.9-slim-bullseye

COPY ./ /tmp/reposter

RUN cd /tmp/reposter && \
    pip install . && \
    cd /tmp && rm -rf reposter

ENV KIJIJI_USERNAME=""
ENV KIJIJI_PASSWORD=""

# Set global envs when running container command:
CMD ["bash", "-c", "echo $(python -m kijiji_repost_headless -u $KIJIJI_USERNAME -p $KIJIJI_PASSWORD repost_all)"]
