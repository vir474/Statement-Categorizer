FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency installation
RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system --no-cache -e .

COPY . .

# Create data directories — pathlib.Path.mkdir handles this too, but belt-and-suspenders
RUN mkdir -p data/uploads

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
