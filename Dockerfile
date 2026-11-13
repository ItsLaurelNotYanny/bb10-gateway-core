FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive \
    DISPLAY=:99 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    APP_HOME=/home/appuser \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    chromium \
    curl \
    dbus-x11 \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    libegl1 \
    libgbm1 \
    libgl1-mesa-dri \
    libgles2 \
    openbox \
    procps \
    python3-aiohttp \
    python3-pil \
    scrot \
    tzdata \
    wmctrl \
    x11-xserver-utils \
    xclip \
    xdotool \
    xvfb \
    && rm -f /etc/chromium.d/extensions \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 1000 appuser && \
    useradd -m -u 1000 -g 1000 -s /bin/bash appuser && \
    mkdir -p /app/presets /app/presets.d /data/profile /certs $APP_HOME/.config/openbox && \
    printf '%s\n' \
      '<?xml version="1.0" encoding="UTF-8"?>' \
      '<openbox_config xmlns="http://openbox.org/3.4/rc">' \
      '  <applications>' \
      '    <application class="*">' \
      '      <decor>no</decor>' \
      '      <position force="yes"><x>0</x><y>0</y></position>' \
      '    </application>' \
      '  </applications>' \
      '</openbox_config>' \
      > $APP_HOME/.config/openbox/rc.xml && \
    chown -R 1000:1000 /app /data /certs $APP_HOME

WORKDIR /app
COPY --chown=1000:1000 presets.py icon_gen.py client_html.py gateway.py healthcheck.py entrypoint.sh /app/
COPY --chown=1000:1000 presets/ /app/presets/
RUN chmod +x /app/entrypoint.sh

USER 1000:1000
EXPOSE 2443
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python3", "/app/healthcheck.py"]

ENTRYPOINT ["/app/entrypoint.sh"]
