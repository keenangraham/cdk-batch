FROM public.ecr.aws/ubuntu/ubuntu:23.10_stable

RUN apt-get update \
    && apt-get install -y ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m aft

WORKDIR /aft

COPY --chown=aft:aft *.sh .

RUN chmod +x *.sh

USER aft

ENTRYPOINT ["./entrypoint.sh"]

CMD ["echo", "Hello"]