FROM python:3.13-slim
WORKDIR /app
# ติดตั้ง uv
RUN pip install uv
# คัดลอกไฟล์ dependencies
COPY pyproject.toml uv.lock ./
# ติดตั้งแพ็กเกจ
RUN uv sync --frozen
# คัดลอกโค้ดทั้งหมด
COPY . .
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]