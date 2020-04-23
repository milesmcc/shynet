<p align="center">
  <h3 align="center">🔭 Shynet 🔭</h3>

  <p align="center">
     Web analytics that's self hosted, cookie free, privacy friendly, and useful(?) 
    <br>
    <br>
    <a href="#installation"><strong>Getting started »</strong></a>
    <br>
  </p>
</p>

## Motivation

There are a _lot_ of web analytics tools. Unfortunately, most of them come with the following caveats:

* They require handing all of your visitors' info to a third-party company
* They use cookies to track visitors across sessions, so you need to have those annoying cookie notices
* They collect so much personal data that even the NSA is jealous
* They are closed source and/or expensive, often with limited data portability
* They are hard to use

Shynet has **none** of these caveats. You host it yourself, so the data is _yours_. It works without cookies, so you don't need any intrusive cookie notices. It collects just enough data to be useful, but not enough to be creepy. It's open source and _intended_ to be self-hosted. And you may even find the interface easy to use.

> **Shynet** is a portmanteau of "Skynet" and "shy." The idea is that it gives you loads of useful information (Skynet) while also respecting your visitors' privacy (shy).

## Screenshots

_Note: These screenshots have been edited to hide sensitive data. The "real" Shynet has a lot more pages and information available, but hopefully this gives you an idea of the general look and feel of the tool._

![Shynet's homepage](images/homepage.png)
_Shynet's homepage, where you can see all of your services at a glance._

Not shown: service view, management view, session view, full service view. (You'll need to install Shynet to see those!)

## Features

#### Architecture

* **Runs on a single machine** &mdash; Because it's so small, Shynet can easily run as a single docker container on a single small VPS.
* **...or across a giant Kubernetes cluster** &mdash; For higher traffic installations, Shynet can be deployed with as many parallelized ingress nodes as needed, with Redis caching and separate backend workers for database IO.
* **Built using Django** &mdash; Shynet is built using Django, so deploying, updating, and migrating can be done without headaches.
* **Multiple users and sites** &mdash; A single Shynet instance can support multiple users, each tracking multiple different sites.

#### Tracking

* **JavaScript not required** &mdash; It will fallback to using a 1x1 transparent tracking pixel if JavaScript isn't available
* **Lightweight** &mdash; The [tracking script](/shynet/analytics/templates/analytics/scripts/page.js) weighs less than a kilobyte (and doesn't look like your typical tracking script)
* **Generally not blocked** &mdash; Because you host Shynet yourself, it tends not to be on ad block lists
* **Primary-key integration** &mdash; You can easily associate visitors in Shynet with their user accounts on your site (if that's something you want)

#### Metrics

Here's the information Shynet can give you about your visitors:

* **Hits** &mdash; how many pages on your site were opened/viewed
* **Sessions** &mdash; how many times your site was visited (essentially a collection of hits)
* **Page load time** &mdash; how long the pages on your site look to load
* **Bounce rate** &mdash; the percentage of visitors who left after just one page
* **Duration** &mdash; how long visitors stayed on the site
* **Referrers** &mdash; the links visitors followed to get to your site
* **Locations** &mdash; the relative popularity of all the pages on your site
* **Operating system** &mdash; your visitors' OS (from user agent)
* **Browser** &mdash; your visitors' browser (from user agent)
* **Geographic location & network** &mdash; general location of your visitors (from IP)
* **Device type** &mdash; whether your visitors are using a desktop, tablet, or phone (from user agent)

#### Workflow
* **Collaboration built-in** &mdash; Administrators can easily share services with other users, as well
* **Accounts (or not)** &mdash; Shynet has a fully featured account management workflow (powered by [Django Allauth](https://github.com/pennersr/django-allauth/)).

## Recommendations

Shynet isn't for everyone. It's great for personal projects and small to medium size websites, but hasn't been tested with ultra-high traffic sites. It's also requires a fair amount of technical know-how to deploy and maintain, so if you need a one-click solution, you're best served with other tools. 

## Concepts

Shynet is pretty simple, but there are a few key terms you need to know in order to use it effectively:

**Services** are the properties on the web you'd like to track. These generally correspond to websites or single top-level domains. Shynet generates one tracking embed per service.

**Hits** are a single page-load on one of your services.

**Sessions** are a collection of hits (or just one) that are made by the same browser in a short period of time.

## Installation

To install Shynet using the simplest possible setup, follow these instructions. Instructions for multi-machine deployments will be available soon.

> **These commands assume Ubuntu.** If you're installing Shynet on a different platform, the process will be different.

1. Pull the latest version of Shynet using `docker pull milesmcc/shynet:latest`. If you don't have Docker installed, [install it](https://docs.docker.com/get-docker/).

2. Have a PostgreSQL server ready to go. This can be on the same machine as the deployment, or elsewhere. You'll just need a username, password, and host. (For info on how to setup a PostgreSQL server on Ubuntu, follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)).

3. Configure an environment file for Shynet. (For example, create a file called `.env`.) Be sure to swap out the variables below with the correct values for your setup. (The comments refer to the lines that follow. Note that Docker is weird with quotes, so it tends to be better to omit them from your env file.)

```
# Database
DB_NAME=<your db name>
DB_USER=<your db user>
DB_PASSWORD=<your db user password>
DB_HOST=<your db host>

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
```

4. Setup the Shynet database by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py migrate`.

5. Create your admin account by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py registeradmin <your email>`. The command will print a temporary password that you'll be able to use to log in.

6. Configure Shynet's hostname (e.g. `shynet.example.com` or `localhost:8000`) by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py hostname "<your hostname>"`. This doesn't affect Shynet's bind port; instead, it determines what hostname to inject into the tracking script. (So you'll want to use the "user-facing" hostname here.)

7. Name your Shynet instance by running `docker run --env-file=<your env file> milesmcc/shynet:latest python manage.py whitelabel "<your instance name>"`. This could be something like "My Shynet Server" or "Acme Analytics"—whatever suits you.

8. Launch the Shynet server by running `docker run --env-file=<your env file> milesmcc/shynet:latest`. You may need to bind Docker's port 8000 (where Shynet runs) to your local port 8000; this can be done using the flag `-p 8080:8080`.

9. Visit your service's homepage, and verify everything looks right! You should see a login prompt. Log in with the credentials from step 5. You'll probably be prompted to "confirm your email"—if you haven't set up an email server, the confirmation email will be printed to the console instead.

10. Create a service by clicking "+ Create Service" in the top right hand corner. Fill out the options as appropriate. Once you're done, press "create" and you'll be redirected to your new service's analytics page.

11. Finally, click on "Manage" in the top right of the service's page to get the tracking script code. Inject this script on all pages you'd like the service to track.

**Next steps:** while out of the scope of this short guide, next steps include setting up Shynet behind a reverse proxy (be it your own [Nginx server](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/) or [Cloudflare](https://cloudflare.com)), making it run in the background, and integrating it on your sites. Integration instructions are available on each service's management page.


## FAQ

**Does Shynet respond to Do Not Track (DNT) signals?** Yes. While there isn't any standardized way to handle DNT requests, Shynet allows you to specify whether you want to collect any data from users with DNT enabled on a per-service basis. (By default, Shynet will _not_ collect any data from users who specify DNT.)

**Is this GDPR compliant?** I think so, but it also depends on how you use it. If you're worried about GDPR, you should talk to a lawyer about your particular data collection practices. I'm not a lawyer. (And this isn't legal advice.)

## Roadmap

The following features are planned:

* **Rollups** (aggregate old data to save space)
* **Anomaly detection** (get email alerts when you get a traffic spike or dip)
* **Interactive traffic heatmap** (see where in the world your visitors are coming from)
* **Better collaboration interface** (the current interface is... a draft)
* **Data deletion tool** (easily prune user data by specifying an ID or IP)
* **Differential privacy** (explore and share your data without revealing any personal information)

## In the Wild

These sites use Shynet to monitor usage without violating visitors' privacy: [PolitiTweet](https://polititweet.org), [Miles' personal site](https://miles.land), [a17t](https://a17t.miles.land), [Lensant](https://lensant.com), [WhoAreMyRepresentatives.org](https://whoaremyrepresentatives.org), and more. (Want to add your site to this list? Send a PR.) 

## Contributing

Are you interested in contributing to Shynet? Just send a pull request! Maybe once the project matures there will be more detailed contribution guidelines, but for now just send the code this way. Just know that by contributing, you agree to share all of your contributions under the same license as the project (see [LICENSE](LICENSE)).

## License

Shynet is made available under the [Apache License, version 2.0](LICENSE).

---

a17t was created by [Miles McCain](https://miles.land) at the [Recurse Center](https://recurse.com) using [a17t](https://a17t.miles.land).
