FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference-neuronx:1.13.1-transformers4.34.1-neuronx-py310-sdk2.15.0-ubuntu20.04

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

RUN mkdir -p /app/docs

COPY sample.txt /app/docs

COPY . .

CMD ["python", "rag.py"]
