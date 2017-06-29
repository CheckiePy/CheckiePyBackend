FROM python:3.5
ENV PYTHONUNBUFFERED 1
COPY requirements.txt /
RUN pip install git+https://github.com/acsproj/acscore.git@0.7
RUN pip install -r requirements.txt
WORKDIR /src/

