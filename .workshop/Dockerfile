# The image Workshop's agents run in when they work on this repository: its standard agent image
# (Debian, Node, Python 3, a C toolchain, git) plus what gamev2's checks need on top of it.
# Workshop builds this from the default branch; only the files directly inside .workshop/ are sent.
ARG WORKSHOP_BASE
FROM ${WORKSHOP_BASE}

USER root

# Pillow for check_generators.py's art tools, which are listed as `skip` without it. The release is the
# one in gamev2/tools/requirements-art.txt, which the Checks workflow installs (that file is not sent to
# this build, so the pin is repeated here: move the two together; tools/tests/check-generators.test.js
# holds them equal). numpy and OpenCV for the photo tools, within gamev2/tools/requirements-photos.txt
# (opencv-contrib for cv2.saliency).
RUN pip install --no-cache-dir --break-system-packages --root-user-action=ignore \
        Pillow==11.3.0 \
        numpy==2.5.5 \
        opencv-contrib-python-headless==4.14.0.94

# playwright-core for the browser regression (gamev2/tools/browser). It downloads no browser: the
# Chromium is Workshop's, on tickets that ask for one.
RUN npm install --global --no-audit --no-fund playwright-core@1.65.1

ENV NODE_PATH=${NODE_PATH:+${NODE_PATH}:}/usr/local/lib/node_modules

# No Japanese font: the art tools set their text in the game's own fonts in gamev2/fonts (#346).

# Fail the build here, not in a later ticket, if any of the above did not take.
RUN set -eux; \
    python3 -c "import PIL, numpy, cv2; assert PIL.__version__ == '11.3.0', PIL.__version__; cv2.saliency"; \
    node -e "require('playwright-core')"

USER agent

LABEL workshop.environment="Adds Pillow 11.3.0 (the pin in gamev2/tools/requirements-art.txt) for the art tools, numpy and OpenCV for the photo tools, and playwright-core 1.65.1 on NODE_PATH for gamev2/tools/browser (which also needs a Chromium). Checks, from gamev2/: node tools/test_game.js; python3 tools/test_blog_to_npc.py; node tools/play.js check; python3 tools/check_generators.py; python3 tools/sync_cities.py --check."
