#
# Copyright 2021 Basislager Services
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

FROM python:3.10-slim

# Install required dependencies.
RUN apt-get update \
 && apt-get install -y \
        chromium \
        chromium-driver \
        curl \
        git \
        texlive-latex-base \
        texlive-latex-extra \
        texlive-latex-recommended \
 && rm -rf /var/lib/apt/lists/*

# Install pandoc from Github.
RUN curl -L -o /tmp/pandoc.deb 'https://github.com/jgm/pandoc/releases/download/2.16.2/pandoc-2.16.2-1-amd64.deb' \
 && dpkg -i /tmp/pandoc.deb \
 && rm -f /tmp/pandoc.deb

# Install the tickergadse package
COPY requirements.txt setup.py /app/
COPY tickergadse /app/tickergadse
RUN pip install /app
RUN rm -rf /app

# Run everything as tickeruser
RUN useradd -ms /bin/bash tickeruser
USER tickeruser
WORKDIR /home/tickeruser

# Setup credentials for Github.
ARG github_name
ARG github_email
ARG github_token
RUN if [ -n "$github_name" ] && [ -n "$github_email" ] && [ -n "$github_token" ]; then \
        git config --global user.name "${github_name}"; \
        git config --global user.email "${github_email}"; \
        git config --global url."https://${github_token}:@github.com/".insteadOf "https://github.com/"; \
    elif [ -n "$github_name" ] || [ -n "$github_email" ] || [ -n "$github_token" ]; then \
        echo "================================================================"; \
        echo "[ERROR] Configuration requires either all Github options or none"; \
        echo "================================================================"; \
        exit 1; \
    fi

COPY docker-entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT ["/docker-entrypoint.sh"]
