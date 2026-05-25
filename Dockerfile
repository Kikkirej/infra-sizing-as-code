FROM asciidoctor/docker-asciidoctor:latest

RUN apk add --no-cache python3 py3-pip nodejs npm && \
    pip3 install pytest --break-system-packages && \
    npm install -g @mermaid-js/mermaid-cli
