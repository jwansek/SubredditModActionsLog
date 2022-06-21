FROM jwansek/subredditmodactionslog
MAINTAINER Eden Attenborough "eddie.atten.ea29@gmail.com"
RUN apt-get install -y cron 
COPY . /app
WORKDIR /app
COPY onceaday/crontab /etc/cron.d/oad-crontab
RUN chmod 0644 /etc/cron.d/oad-crontab && crontab /etc/cron.d/oad-crontab
RUN pip3 install -r onceaday/requirements.txt
ENTRYPOINT ["cron", "-f"]
