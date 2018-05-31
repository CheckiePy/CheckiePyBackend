# Hosts for running the application in a local environment

# HOSTNAME = '127.0.0.1'
# POSTGRES_HOST = 'localhost'
# RABBITMQ_HOST = 'localhost'


# Hosts for running the application in a Docker container
# HOSTNAME and WEBHOOK_HOST should be set according to your domain or server IP address

HOSTNAME = 'checkiepy.com'
POSTGRES_HOST = 'postgres'
RABBITMQ_HOST = 'rabbitmq'


# Replace 'https' with 'http' if you don't use a secure connection

WEBHOOK_HOST = 'https://checkiepy.com'
