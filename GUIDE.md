# Usage Guide

## Table of Contents

- [Installation](#installation)
- [Heroku](#heroku)
- [Render](#render)
- [Updating Your Configuration](#updating-your-configuration)
- [Advanced Usage](#advanced-usage)
  * [Configuring a Reverse Proxy](#configuring-a-reverse-proxy)
    + [Cloudflare](#cloudflare)
    + [Nginx](#nginx)
  * [Health Checks](#health-checks)
  * [Primary Key Integration](#primary-key-integration)
  * [Usage with Single-Page Applications](#usage-with-single-page-applications)
+ [Troubleshooting](#troubleshooting)
---

## Staying Updated

**If you install Shynet, you should strongly consider enabling notifications when new versions are released.** You can do this under the "Watch" tab on GitHub (above). This will ensure that you are notified when new versions are available, some of which may be security updates. (Shynet will never automatically update itself.)

> **When you do update, read the release notes!** These will tell you if you need to make changes to your deployment. (E.g., Shynet 0.13.1 requires additional configuration.)

## Installation

Installation of Shynet is easy! Follow the [Basic Installation](#basic-installation) guide or the [Basic Installation with Docker Compose](#basic-installation-with-docker-compose) below for a minimal installation, or if you are going to be running Shynet over HTTPS through a reverse proxy.

> **These commands assume Ubuntu.** If you're installing Shynet on a different platform, the process will be different.

Before continuing, please be sure to have the latest version of Docker installed.

### Basic Installation

1. Pull the latest version of Shynet using `docker pull milesmcc/shynet:latest`. If you don't have Docker installed, [install it](https://docs.docker.com/get-docker/).

2. For database you can use either PostgreSQL or SQLite:

    2.1 To use PostgreSQL you need a server ready to go. This can be on the same machine as the deployment, or elsewhere. You'll need a username, password, host, and port, set in the appropriate `DB_` environment variables (see next). (For info on how to setup a PostgreSQL server on Ubuntu, follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

    2.2 SQLite doesn't need a server, just a file. Set `SQLITE=True` in the environment file and create a Docker volume to hold the persistent DB with `docker volume create shynet_db`. Then whenever you run the container include `-v shynet_db:/var/local/shynet/db:rw` to mount the volume into the container. See the [Docker documentation on volumes](https://docs.docker.com/storage/volumes/).

3. Configure an environment file for Shynet, using [this file](/TEMPLATE.env) as a template. (This file is typically named `.env`.) Make sure you set the database settings, or Shynet won't be able to run. Also consider setting `ALLOWED_HOSTS` inside the environment file to your deployment's domain for better security.

4. Launch the Shynet server for the first time by running `docker run --env-file=<your env file> milesmcc/shynet:latest`. Provided you're using the default environment information (i.e., `PERFORM_CHECKS_AND_SETUP` is `True`), you'll see a few warnings about not having an admin user or host setup; these are normal. Don't worry — we'll do this in the next step. You only need to stop if you see a stacktrace about being unable to connect to the database.

5. Create an admin user by running `docker run --env-file=<your env file> milesmcc/shynet:latest ./manage.py registeradmin <your email>`. A temporary password will be printed to the console.

6. Set the whitelabel of your Shynet instance by running `docker run --env-file=<your env file> milesmcc/shynet:latest ./manage.py whitelabel <whitelabel>`. While this setting doesn't affect any core operations of Shynet, it lets you rename Shynet to whatever you want. (Example whitelabels: `"My Shynet Instance"` or `"Acme Analytics"`.)

7. Launch your webserver by running `docker run --env-file=<your env file> milesmcc/shynet:latest`. You may need to bind Docker's port 8080 (where Shynet runs) to your local port 80 (http); this can be done using the flag `-p 80:8080` after `run`. Visit your service's homepage, and verify everything looks right! You should see a login prompt. Log in with the credentials from step 5. You'll probably be prompted to "confirm your email"—if you haven't set up an email server, the confirmation email will be printed to the console instead.

8. Create a service by clicking "+ Create Service" in the top right hand corner. Fill out the options as appropriate. Once you're done, press "create" and you'll be redirected to your new service's analytics page.

9. Finally, click on "Manage" in the top right of the service's page to get the tracking script code. Inject this script on all pages you'd like the service to track.


### Basic Installation with Docker Compose

> Make sure you have `docker-compose` installed. If not, [install it](https://docs.docker.com/compose/install/) 

1. Clone the repository.

2. Using [TEMPLATE.env](/TEMPLATE.env) as a template, configure the environment for your Shynet instance and place the modified config in a file called `.env` in the root of the repository. Do _not_ change the port number at the end; you can set the public facing port in the next step. 

3. On line 2 of the `nginx.conf` file located in the root of the repository, replace `example.com` with your hostname. Then, in the `docker-compose.yml` file, set the port number by replacing `8080` in line 38 ( `- 8080:80` ) with whatever local port you want to bind it to. For example, set the port number to `- 80:80` if you want your site will be available via HTTP (port 80) at `http://<your hostname>`.

4. Launch the Shynet server for the first time by running `docker-compose up -d`. If you get an error like "permission denied" or "Couldn't connect to Docker daemon", either prefix the command with `sudo` or add your user to the `docker` group.

5. Create an admin user by running `docker exec -it shynet_main ./manage.py registeradmin <your email>`. A temporary password will be printed to the console.

6. Set the whitelabel of your Shynet instance by running `docker exec -it shynet_main ./manage.py whitelabel <whitelabel>`. While this setting doesn't affect any core operations of Shynet, it lets you rename Shynet to whatever you want. (Example whitelabels: "My Shynet Instance" or "Acme Analytics".)

Your site should now be accessible at `http://hostname:port`. Now you can follow steps 9-10 of the [Basic Installation](#basic-installation) guide above to get Shynet integrated on your sites.

## Heroku

You may wish to deploy Shynet on Heroku. Note that Heroku's free offerings (namely the free Postgres addon) are unlikely to support running any Shynet instance that records more than a few hundred requests per day &mdash; the database will quickly fill up. In most cases, the more cost-effective option for running Shynet is renting a VPS from a full cloud service provider. However, if you're sure Heroku is the right option for you, or you just want to try Shynet out, you can use the Quick Deploy button then follow the steps below. 

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/milesmcc/shynet/tree/master)

Once you deploy, you'll need to setup an admin user and whitelabel before you can use Shynet. Do that with the following commands:

1. `heroku run --app=<your app> ./manage.py registeradmin <your email>`
2. `heroku run --app=<your app> ./manage.py whitelabel "<your Shynet instance's name>"`

## Render

[Render](https://render.com) is a modern cloud platform to build and run all your apps and websites with free SSL, a global CDN, private networks and auto deploys from Git. To deploy Shynet, click the `Deploy to Render` button and follow the steps below.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/shynet)

Once your deploy has completed, use the **Render Shell** to configure your app:

1. Set your email: `./manage.py registeradmin your-email@example.com`
2. Set your whitelabel: `./manage.py whitelabel "Your Shynet Instance Name"`

See the [Render docs](https://render.com/docs/deploy-shynet) for more information on deploying your application on Render.

---

## Advanced Usage

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
           proxy_set_header X-Real-IP $remote_addr;
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

### Health Checks

By default, Shynet includes a default health check endpoint at `/healthz/`. If the instance is running normally, this endpoint will return an HTTP status code of 200; if something is wrong, it will have a non-200 status code. To view the health data as JSON, send your request to `/healthz/?format=json`.

This feature is helpful when running Shynet with Kubernetes, as it allows you to setup [startup readiness probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) that prevent traffic from being sent to your Shynet instances before they are ready.

### Primary-Key Integration

In some cases, it is useful to associate particular users on your platform with their sessions in Shynet. In Shynet, this is called _primary key integration_, and is done by adding an additional element to the Shynet script url for each particular user.

If the Shynet script location (for either the pixel or the script) is, for example, `//shynet.example.com/ingress/your_service_uuid/pixel.gif` and `//shynet.example.com/ingress/your_service_uuid/script.js`, the URLs for primary-key enabled users would be `//shynet.example.com/ingress/your_service_uuid/USER_PRIMARY_KEY/pixel.gif` and `//shynet.example.com/ingress/your_service_uuid/USER_PRIMARY_KEY/script.js`.

Adding this path can be done easily using server-side rendering. For example, here is a Django template that adds users' primary keys to the Shynet tracking script:

```html
{% if request.user.is_authenticated %}
<noscript>
   <img src="//shynet.example.com/ingress/service-uuid/{{request.user.email|urlencode:""}}/pixel.gif">
</noscript>
<script src="//shynet.example.com/ingress/service-uuid/{{request.user.email|urlencode:""}}/script.js"></script>
{% else %}
<noscript>
   <img src="//shynet.example.com/ingress/service-uuid/pixel.gif">
</noscript>
<script src="//shynet.example.com/ingress/service-uuid/script.js"></script>
{% endif %}
```

### Usage with Single-Page Applications

In a single-page application, the page never reloads. (That's the entire point of single-page applications, after all!) Unfortunately, this also means that Shynet will not automatically recognize and track when the user navigates between pages _within_ your application.

Fortunately, Shynet offers a simple method you can call from anywhere within your JavaScript to indicate that a new page has been loaded: `Shynet.newPageLoad()`. Add this method call to the code that handles routing in your app, and you'll be ready to go.


### API

All the information displayed on the dashboard can be obtained via API on url ```//shynet.example.com/api/v1/dashboard/```. By default this endpoint will return the full data from all services over the last last 30 days. The `Authentication` header should be set to use user's personal API token (```'Authorization: Token <user API token>'```).

There are 3 optional query parameters:
 * `uuid` - to get data only from one service
 * `startDate` - to set start date in format YYYY-MM-DD
 * `endDate` - to set end date in format YYYY-MM-DD

Example in HTTPie:
```http get '//shynet.example.com/api/v1/dashboard/?uuid={{service_uuid}}&startDate=2021-01-01&endDate=2050-01-01' 'Authorization:Token {{user_api_token}}'```

Example in cURL:
```curl -H 'Authorization:Token {{user_api_token}}' '//shynet.example.com/api/v1/dashboard/?uuid={{service_uuid}}&startDate=2021-01-01&endDate=2050-01-01'```

---

## Troubleshooting

Here are solutions for some common issues. If your situation isn't described here or the solution didn't work, feel free to [create an issue](https://github.com/milesmcc/shynet/issues/new) (but be sure to check for duplicate issues first).

#### The admin panel works, but no page views are showing up!

* If you are running a single Shynet webserver instance (i.e., you followed the default installation instructions), verify that you haven't set `CELERY_TASK_ALWAYS_EAGER` to `False` in your environment file.
* Verify that your cache is properly configured. In single-instance deployments, this means making sure that you haven't set any `REDIS_*` or `CELERY_*` environment variables (those are for more advanced deployments; you'll just want the defaults).
* If your service is configured to respect Do Not Track (under "Advanced Settings"), verify that your browser isn't sending the `DNT=1` header with your requests (or temporarily disable DNT support in Shynet while testing). Sometimes, an adblocker or privacy browser extension will add this header to requests unexpectedly.

#### Shynet isn't linking different pageviews from the same visitor into a single session!

* Verify that your cache is properly configured. (See #2 above.) In multi-instance deployments, it's critical that all webservers are using the _same_ cache—so make sure you configure a Redis cache if you're using a non-default installation.
* This can happen between Shynet restarts if you're not using an external cache provider (like Redis).

#### I changed the `SHYNET_WHITELABEL`/`SHYNET_HOST` environment variable, but nothing happened!

* Those values only affect how your Shynet instance is setup on first run; once it's configured, they have no effect. See [updating your configuration](#updating-your-configuration) for help on how to update your configuration. (Note: these environment variables are not present in newer Shynet versions; they have been removed from the guide.)

#### Shynet can't connect to my database running on `localhost`/`127.0.0.1`

* The problem is likely that to Shynet, `localhost` points to the local network in the container itself, not on the host machine. Try adding the `--network='host'` option when you run Docker.
