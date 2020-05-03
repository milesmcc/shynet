# Usage Guide

## Table of Contents

- [Installation](#installation)
- [Updating Your Configuration](#updating-your-configuration)
- [Enhancements](#enhancements)
  * [Installation with SSL](#installation-with-ssl)
  * [Configuring a Reverse Proxy](#configuring-a-reverse-proxy)
    + [Cloudflare](#cloudflare)
    + [Nginx](#nginx)
+ [Troubleshooting](#troubleshooting)

---

## Installation

Installation of Shynet is easy! Follow the [Basic Installation](#basic-installation) guide below if you'd like to run Shynet over HTTP or if you are going to be running it over HTTPS through a reverse proxy. If you'd like to run Shynet over HTTPS without a reverse proxy, skip ahead to [Installation with SSL](#installation-with-ssl) instead.

> **These commands assume Ubuntu.** If you're installing Shynet on a different platform, the process will be different.

Before continuing, please be sure to have the latest version of Docker installed.

### Basic Installation

1. Pull the latest version of Shynet using `docker pull milesmcc/shynet:latest`. If you don't have Docker installed, [install it](https://docs.docker.com/get-docker/).

2. Have a PostgreSQL server ready to go. This can be on the same machine as the deployment, or elsewhere. You'll just need a username, password, host, and port. (For info on how to setup a PostgreSQL server on Ubuntu, follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

3. Configure an environment file for Shynet, using [this file](/TEMPLATE.env) as a template. (This file is typically named `.env`.) Make sure you set the database settings, or Shynet won't be able to run.

4. Launch the Shynet server by running `docker run --env-file=<your env file> milesmcc/shynet:latest`. Watch the output of the script; if it's the first run, you'll see a temporary password printed that you can use to log in. You may need to bind Docker's port 8080 (where Shynet runs) to your local port 80 (http); this can be done using the flag `-p 80:8080` after `run`.

5. Visit your service's homepage, and verify everything looks right! You should see a login prompt. Log in with the credentials from step 4. You'll probably be prompted to "confirm your email"—if you haven't set up an email server, the confirmation email will be printed to the console instead.

6. Create a service by clicking "+ Create Service" in the top right hand corner. Fill out the options as appropriate. Once you're done, press "create" and you'll be redirected to your new service's analytics page.

7. Finally, click on "Manage" in the top right of the service's page to get the tracking script code. Inject this script on all pages you'd like the service to track.

## Updating Your Configuration

When you first setup Shynet, you set a number of environment variables that determine first-run initialization settings (these variables start with `SHYNET_`). Once they're first set, though, changing them won't have any effect. Be sure to run the following commands in the same way that you deploy Shynet (i.e., linked to the same database).

* Create an admin account by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py registeradmin <your email>`. The command will print a temporary password that you'll be able to use to log in.

* Configure Shynet's hostname (e.g. `shynet.example.com` or `localhost:8000`) by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py hostname "<your hostname>"`. This doesn't affect Shynet's bind port; instead, it determines what hostname to inject into the tracking script. (So you'll want to use the "user-facing" hostname here.)

* Name your Shynet instance by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py whitelabel "<your instance name>"`. This could be something like "My Shynet Server" or "Acme Analytics"—whatever suits you.

---

## Enhancements


### Installation with SSL

If you are going to be running Shynet through a reverse proxy, please see [Configuring a Reverse Proxy](#configuring-a-reverse-proxy) instead.

0. We'll be cloning this into the home directory to make this installation easier, so run `cd ~/` if you need to.

1. Instead of pulling from Docker, we will be pulling from GitHub and building using Docker in order to easily add SSL certificates. You will want to run `git clone https://github.com/milesmcc/shynet.git` to clone the GitHub repo to your current working directory.

2. To install `certbot` follow [the guide here](https://certbot.eff.org/instructions) or follow along below
   * Ubuntu 18.04
     * `sudo apt-get update`
     * `sudo apt-get install software-properties-common`
     * `sudo add-apt-repository universe`
     * `sudo add-apt-repository ppa:certbot/certbot`
     * `sudo apt-get update`
     * `sudo apt-get install certbot`

3. Run `sudo certbot certonly --standalone` and follow the instructions to generate your SSL certificate.
   * If you registering the certificate to a domain name like `example.com`, please be sure to point your DNS records to your current server before running `certbot`.

4. We are going to move the SSL certificates to the Shynet repo with with command below. Replace `<domain>` with the domain name you used in step 3.
   * `cp /etc/letsencrypt/live/<domain>/{cert,privkey}.pem ~/shynet/shynet/`

5. With that, we are going to replace the `webserver.sh` with `ssl.webserver.sh` to enable the use of SSL certificates. The original `webserver.sh` will be backed up to `backup.webserver.sh`
   * `mv ~/shynet/shynet/webserver.sh ~/shynet/shynet/backup.webserver.sh`
   * `mv ~/shynet/shynet/ssl.webserver.sh ~/shynet/shynet/webserver.sh`

6. Now we build the image!
   * `docker image build shynet -t shynet-ssl:latest`

7. Have a PostgreSQL server ready to go. This can be on the same machine as the deployment, or elsewhere. You'll just need a username, password, host, and port (default is `5432`). (For info on how to setup a PostgreSQL server on Ubuntu, follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

8. Follow the [Basic Installation](#basic-installation) guide with just one modification: in step #4, change the local bind port from `80` to `443`, and use `shynet-ssl:latest` as your Docker image instead of `milesmcc/shynet:latest`.

### Configuring a Reverse Proxy

A reverse proxy has many benefits. It can be used for DDoS protection, caching files to reduce server load, routing HTTPS and/or HTTP connections, hosting multiple services on a single server, [and more](https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/)!

#### Cloudflare

[Cloudflare](https://www.cloudflare.com/) is a great reverse proxy option. It's free, automatically configures HTTPs, offers out-of-the-box security features, provides DNS, and requires minimal setup.

1. Follow Cloudflare's [getting started guide](https://support.cloudflare.com/hc/en-us/articles/201720164-Creating-a-Cloudflare-account-and-adding-a-website).

2. After setting up Cloudflare, here are a few things you should consider doing:
   * Under the `SSL` Tab > `Overview` > Change your `SSL/TLS Encryption Mode` to `Flexible`
   * The following will block your admin panel from anyone who isn't on your IP address. This is optional, but great for security.
     * Under the `Firewall` tab > `Overview` > `+ Create Firewall Rule`:
     * Name: `Admin Panel Restriction`
     * Field: `URI Path`
     * Operator: `equals`
     * Value: `/admin`
     * Click `AND`
     * Field: `IP Address`
     * Operator: `does not equal`
     * Value: `<your public IP address>`
     * Then: `Block`

#### Nginx

Nginx is a self hosted, highly configurable webserver. Nginx can be configured to run as a reverse proxy on either the same machine or a remote machine.

##### Set up

> **These commands assume Ubuntu.** If you're installing Nginx on a different platform, the process will be different.

0. Before starting, shut down your Docker containers (if any are running)
   * Run `docker container ls` to find the container ID
   * Run `docker stop <container id from the last step>`

1. Update your packages and install Nginx
   * `sudo apt-get update`
   * `sudo apt-get install nginx`

2. Disable the default Nginx placeholder
   * `sudo unlink /etc/nginx/sites-enabled/default`

3. Create the Nginx reverse proxy config file
   * `cd /etc/nginx/sites-available/`
   * `vi reverse-proxy.conf` or `nano reverse-proxy.conf`
   * Paste the following configuration into that file:

   ```nginx
   # Know what you're pasting! Read the Reference!
   # Reference: https://nginx.org/en/docs/
   server {
       listen 80;
       location / {
           proxy_pass http://127.0.0.1:8080;
       }
   }
   ```

   * Save and exit the text editor
     * `:wq` for vi
     * `ctrl+x` then `y` for nano
   * Link Nginx's `sites-enabled` to read the new config
     * `sudo ln -s /etc/nginx/sites-available/reverse-proxy.conf /etc/nginx/sites-enabled/reverse-proxy.conf`
   * Make sure the config is working
     * `service nginx configtest`
     * `service nginx restart`

4. Restart your Docker image, but this time use `8080` as the local bind port, as that's where we configured Nginx to look
   * `cd ~/`
   * `docker run -p 8080:8080 --env-file=<your env file> milesmcc/shynet:latest`

5. Finally, time to test!
   * Go to `http://<your site>/admin`

6. If everything is working as expected, please read through some of the following links below to customize Nginx
   * [How to add SSL/HTTPS to Nginx (Ubuntu 18.04)](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-18-04)
   * [How to add SSL/HTTPS to Nginx (Ubuntu 16.04)](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04)
   * [Nginx Documentation](https://nginx.org/en/docs/)

---

## Troubleshooting

Here are solutions for some common issues. If your situation isn't described here or the solution didn't work, feel free to [create an issue](https://github.com/milesmcc/shynet/issues/new) (but be sure to check for duplicate issues first).

#### The admin panel works, but no page views are showing up!

* If you are running a single Shynet webserver instance (i.e., you followed the default installation instructions), verify that you haven't set `CELERY_TASK_ALWAYS_EAGER` to `False` in your environment file.
* Verify that your cache is properly configured. In single-instance deployments, this means making sure that you haven't set any `REDIS_*` or `CELERY_*` environment variables (those are for more advanced deployments; you'll just want the defaults).
* If your service is configured to respect Do Not Track (under "Advanced Settings"), verify that your browser isn't sending the `DNT=1` header with your requests (or temporarily disable DNT support in Shynet while testing). Sometimes, an adblocker or privacy browser extension will add this header to requests unexpectedly.

#### Shynet isn't linking different pageviews from the same visitor into a single session!

* Verify that your cache is properly configured. (See #2 above.) In multi-instance deployments, it's critical that all webservers are using the _same_ cache—so make sure you configure a Redis cache if you're using a non-default installation.

#### I changed the `SHYNET_WHITELABEL`/`SHYNET_HOST` environment variable, but nothing happened!

* Those values only affect how your Shynet instance is setup on first run; once it's configured, they have no effect. See [updating your configuration](#updating-your-configuration) for help on how to update your configuration.
