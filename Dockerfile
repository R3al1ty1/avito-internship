FROM gradle:4.7.0-jdk8-alpine AS build
COPY --chown=gradle:gradle . /home/gradle/src
WORKDIR /home/gradle/src
RUN gradle build --no-daemon 

FROM openjdk:8-jre-slim

EXPOSE 8080

RUN mkdir /app

COPY --from=build /home/gradle/src/build/libs/*.jar /app/spring-boot-application.jar

ENTRYPOINT ["java", "-XX:+UnlockExperimentalVMOptions", "-XX:+UseCGroupMemoryLimitForHeap", "-Djava.security.egd=file:/dev/./urandom","-jar","/app/spring-boot-application.jar"]

FROM python:3.12-slim

WORKDIR /backend/apps

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код приложения
COPY . .

# Указываем переменную окружения для Django
ENV DJANGO_SETTINGS_MODULE=backend.tenders_app.settings

# Открываем порт 8000
EXPOSE 8080

# Запуск миграций и сервера
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8080"]
