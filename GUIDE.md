<p align="center">
  <h3 align="center">🔭 Shynet 🔭</h3>

  <p align="center">
     Web analytics that's self hosted, cookie free, privacy friendly, and useful(?) 
    <br>
  </p>
</p>

## Table of Contents

* [Installation](#installation)
  * [Basic Installation](#basic-installation)
  * [Installation with SSL](#installation-with-ssl)
<!--
* Usage
  * Adding Shynet tracking to your first website
  * Adding a new website
  * Adding a new administrator
* Setting up a reverse proxy
  * Cloudflare
  * nginx
-->

## Installation

Installation of Shynet is easy! Follow the [Basic Installation](#basic-installation) guide below if you'd like to run Shynet over HTTP or if you are going to be running it over HTTPS through a reverse proxy. If you'd like to run Shynet over HTTPS without a reverse proxy, skip ahead to [Installation with SSL](#installation-with-ssl) instead.

> **These commands assume Ubuntu.** If you're installing Shynet on a different platform, the process will be different.

Before continuing, please be sure to have the latest version of Docker installed.

### Basic Installation

1. Pull the latest version of Shynet using `docker pull milesmcc/shynet:latest`. If you don't have Docker installed, [install it](https://docs.docker.com/get-docker/).

2. Have a PostgreSQL server ready to go. This can be on the same machine as the deployment, or elsewhere. You'll just need a username, password, host, and port (default is `5432`). (For info on how to setup a PostgreSQL server on Ubuntu, follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

3. Configure an environment file for Shynet. (For example, create a file called `.env`.) Be sure to swap out the variables below with the correct values for your setup. (The comments refer to the lines that follow. Note that Docker is weird with quotes, so it tends to be better to omit them from your env file.)

```
# Database
DB_NAME=<your db name>
DB_USER=<your db user>
DB_PASSWORD=<your db user password>
DB_HOST=<your db host>
DB_PORT=<your db port>

# General Django settings
DJANGO_SECRET_KEY=<your Django secret key; just a random string>
# Don't leak error details to visitors, very important
DEBUG=False
CELERY_TASK_ALWAYS_EAGER=True 
# For better security, set this to your deployment's domain. Comma separated.
ALLOWED_HOSTS=*
# Set to True (capitalized) if you want people to be able to sign up for your Shynet instance (not recommended)
SIGNUPS_ENABLED=False
# Change as required
TIME_ZONE=America/New_York
# Set to "False" if you will not be serving content over HTTPS
SCRIPT_USE_HTTPS=True
```

For more advanced deployments, you may consider adding the following settings to your environment file. **The following settings are optional, and not required for simple deployments.**

```env
# Email settings
EMAIL_HOST_USER=<your SMTP email user>
EMAIL_HOST_PASSWORD=<your SMTP email password>
EMAIL_HOST=<your SMTP email hostname>
SERVER_EMAIL=Shynet <noreply@shynet.example.com>

# Redis and queue settings; not necessary for single-instance deployments
REDIS_CACHE_LOCATION=redis://redis.default.svc.cluster.local/0 
# If set, make sure CELERY_TASK_ALWAYS_EAGER is False
CELERY_BROKER_URL=redis://redis.default.svc.cluster.local/1

# Other Shynet settings 
# How frequently should the monitoring script "phone home" (in ms)?
SCRIPT_HEARTBEAT_FREQUENCY=5000
# Should only superusers (admins) be able to create services? This is helpful
# when you'd like to invite others to your Shynet instance but don't want
# them to be able to create services of their own.
ONLY_SUPERUSERS_CREATE=False
```

4. Setup the Shynet database by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py migrate`.

5. Create your admin account by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py registeradmin <your email>`. The command will print a temporary password that you'll be able to use to log in.

6. Configure Shynet's hostname (e.g. `shynet.example.com` or `localhost:8000`) by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py hostname "<your hostname>"`. This doesn't affect Shynet's bind port; instead, it determines what hostname to inject into the tracking script. (So you'll want to use the "user-facing" hostname here.)

7. Name your Shynet instance by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py whitelabel "<your instance name>"`. This could be something like "My Shynet Server" or "Acme Analytics"—whatever suits you.

8. Launch the Shynet server by running `docker run --env-file=<your env file> milesmcc/shynet:latest`. You may need to bind Docker's port 8080 (where Shynet runs) to your local port 80 (http); this can be done using the flag `-p 80:8080` after `run`.

9. Visit your service's homepage, and verify everything looks right! You should see a login prompt. Log in with the credentials from step 5. You'll probably be prompted to "confirm your email"—if you haven't set up an email server, the confirmation email will be printed to the console instead.

10. Create a service by clicking "+ Create Service" in the top right hand corner. Fill out the options as appropriate. Once you're done, press "create" and you'll be redirected to your new service's analytics page.

11. Finally, click on "Manage" in the top right of the service's page to get the tracking script code. Inject this script on all pages you'd like the service to track.

### Installation with SSL

If you are going to be running Shynet through a reverse proxy, please use the [Basic Installation](#basic-installation) guide instead.

0. We'll be cloning this into the home directory to make this installation easier, so run `cd ~/` if you need to.

1. Instead of pulling from Docker, we will be pulling from GitHub and building in Docker so that we may easily add SSL certificates. You will want to run `git clone https://github.com/milesmcc/shynet.git` to clone the GitHub repo to your computer.

2. To install `certbot` follow [the guide here](https://certbot.eff.org/instructions) or follow along below
   * Ubuntu 18.04
     * `sudo apt-get update`
     * `sudo apt-get install software-properties-common`
     * `sudo add-apt-repository universe`
     * `sudo add-apt-repository ppa:certbot/certbot`
     * `sudo apt-get update`
     * `sudo apt-get install certbot`

3. Run `sudo certbot certonly --standalone` and follow the instructions to generate your SSL certificate.
   * If you registering it to a domain name like `example.com`, please be sure to point your DNS records to your server before running `certbot`.

4. We are going to move the SSL certificates to the Shynet repo with with command below. Replace `<domain>` with the domain name you used in step 3.
   * `cp /etc/letsencrypt/live/<domain>/{cert,privkey}.pem ~/shynet/shynet/`

5. With that, we are going to replace the `webserver.sh` with `ssl.webserver.sh` to enable the use of SSL certificates. The original `webserver.sh` will be backed up to `backup.webserver.sh`
   * `mv ~/shynet/shynet/webserver.sh ~/shynet/shynet/backup.webserver.sh`
   * `mv ~/shynet/shynet/ssl.webserver.sh ~/shynet/shynet/webserver.sh`

6. Now we build the image!
   * `docker image build shynet -t milesmcc/shynet:latest-ssl`

7. Have a PostgreSQL server ready to go. This can be on the same machine as the deployment, or elsewhere. You'll just need a username, password, host, and port (default is `5432`). (For info on how to setup a PostgreSQL server on Ubuntu, follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

8. Configure an environment file for Shynet. (For example, create a file called `.env`.) Be sure to swap out the variables below with the correct values for your setup. (The comments refer to the lines that follow. Note that Docker is weird with quotes, so it tends to be better to omit them from your env file.)

```
# Database
DB_NAME=<your db name>
DB_USER=<your db user>
DB_PASSWORD=<your db user password>
DB_HOST=<your db host>
DB_PORT=<your db port>

# General Django settings
DJANGO_SECRET_KEY=<your Django secret key; just a random string>
# Don't leak error details to visitors, very important
DEBUG=False
CELERY_TASK_ALWAYS_EAGER=True 
# For better security, set this to your deployment's domain. Comma separated.
ALLOWED_HOSTS=*
# Set to True (capitalized) if you want people to be able to sign up for your Shynet instance (not recommended)
SIGNUPS_ENABLED=False
# Change as required
TIME_ZONE=America/New_York
# Set to "False" if you will not be serving content over HTTPS
SCRIPT_USE_HTTPS=True
```

For more advanced deployments, you may consider adding the following settings to your environment file. **The following settings are optional, and not required for simple deployments.**

```env
# Email settings
EMAIL_HOST_USER=<your SMTP email user>
EMAIL_HOST_PASSWORD=<your SMTP email password>
EMAIL_HOST=<your SMTP email hostname>
SERVER_EMAIL=Shynet <noreply@shynet.example.com>

# Redis and queue settings; not necessary for single-instance deployments
REDIS_CACHE_LOCATION=redis://redis.default.svc.cluster.local/0 
# If set, make sure CELERY_TASK_ALWAYS_EAGER is False
CELERY_BROKER_URL=redis://redis.default.svc.cluster.local/1


# Other Shynet settings 
# How frequently should the monitoring script "phone home" (in ms)?
SCRIPT_HEARTBEAT_FREQUENCY=5000
# Should only superusers (admins) be able to create services? This is helpful
# when you'd like to invite others to your Shynet instance but don't want
# them to be able to create services of their own.
ONLY_SUPERUSERS_CREATE=False
```

9. Setup the Shynet database by running `docker run --env-file=<your env file> milesmcc/shynet:latest-ssl python manage.py migrate`.

10. Create your admin account by running `docker run --env-file=<your env file> milesmcc/shynet:latest-ssl python manage.py registeradmin <your email>`. The command will print a temporary password that you'll be able to use to log in.

11. Configure Shynet's hostname (e.g. `shynet.example.com` or `localhost:8000`) by running `docker run --env-file=<your env file> milesmcc/shynet:latest-ssl python manage.py hostname "<your hostname>"`. This doesn't affect Shynet's bind port; instead, it determines what hostname to inject into the tracking script. (So you'll want to use the "user-facing" hostname here.)

12. Name your Shynet instance by running `docker run --env-file=<your env file> milesmcc/shynet:latest-ssl python manage.py whitelabel "<your instance name>"`. This could be something like "My Shynet Server" or "Acme Analytics"—whatever suits you.

13. Launch the Shynet server by running `docker run --env-file=<your env file> milesmcc/shynet:latest-ssl`. You may need to bind Docker's port 8080 (where Shynet runs) to your local port 443 (https); this can be done using the flag `-p 443:8080` after `run`.

14. Visit your service's homepage using `https://`, and verify everything looks right! You should see a login prompt. Log in with the credentials from step 10. You'll probably be prompted to "confirm your email"—if you haven't set up an email server, the confirmation email will be printed to the console instead.

15. Create a service by clicking "+ Create Service" in the top right hand corner. Fill out the options as appropriate. Once you're done, press "create" and you'll be redirected to your new service's analytics page.

16. Finally, click on "Manage" in the top right of the service's page to get the tracking script code. Inject this script on all pages you'd like the service to track.

---

**Next steps:** while out of the scope of this short guide, next steps include setting up Shynet behind a reverse proxy (be it your own [Nginx server](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) or [Cloudflare](https://cloudflare.com)), making it run in the background, and integrating it on your sites. Integration instructions are available on each service's management page.