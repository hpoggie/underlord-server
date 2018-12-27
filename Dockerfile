# Run with `docker run -p 9099:9099 aircontrol/underlord-server`
from python:3.7.1

COPY . .
RUN pip install -r requirements.txt

EXPOSE 9099

CMD ["python", "lobbyServer.py"]
